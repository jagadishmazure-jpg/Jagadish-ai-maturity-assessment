"""The assessor agent graph: load -> collect -> score -> explain -> verify -> review -> rollup ->
gaps -> roadmap. Every node is deterministic; the only "model" is ``MockLLM``.

    from aimaturity.agents.assessor import assess
    result = assess("portfolio")             # snapshot evidence, checked-in reviews
    result = assess("portfolio", live=True)  # scan sibling checkouts read-only
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

from aimaturity.agents.graph import END, StateGraph
from aimaturity.agents.llm import MockLLM, cited_ids, claimed_level, template_rationale
from aimaturity.gaps import gap_analysis
from aimaturity.hitl import apply_reviews, queue, read_log, read_reviews, verify_audit_log
from aimaturity.orgs import gather, load_org
from aimaturity.roadmap import schedule, work_items
from aimaturity.rollup import overall, pillar_rollup
from aimaturity.scoring import score_all

NODES = ["load", "collect", "score", "explain", "verify", "review", "rollup", "gaps", "roadmap"]


def _load(s):
    org = load_org(s["org_id"])
    return {**s, "org": org}


def _collect(s):
    ev = s.get("evidence_override") or gather(s["org"], live=s.get("live", False), root=s.get("root"))
    return {**s, "evidence": ev, "evidence_by_id": {e.id: e for e in ev}}


def _score(s):
    scanned = bool(s["org"].repo_names())
    return {**s, "results": score_all(s["evidence"], scanned_repos=scanned)}


def _facts(res) -> dict[str, Any]:
    return {"level": res.level, "evidence": res.evidence, "missing": res.next_missing, "confidence": res.confidence}


def _explain(s):
    llm: MockLLM = s["llm"]
    return {**s, "rationales": {cid: llm.rationale(_facts(r)) for cid, r in s["results"].items()}}


def _verify(s):
    """Reject rationales that cite unknown evidence, cite evidence outside the category, or claim another level."""
    issues, fixed = [], {}
    for cid, text in s["rationales"].items():
        res = s["results"][cid]
        cites = cited_ids(text)
        bad = [c for c in cites if c not in s["evidence_by_id"]]
        foreign = [c for c in cites if c in s["evidence_by_id"] and c not in res.evidence]
        lvl = claimed_level(text)
        problems = []
        if bad:
            problems.append(f"unknown evidence {bad}")
        if foreign:
            problems.append(f"evidence not used by this category {foreign}")
        if lvl != res.level:
            problems.append(f"claims level {lvl}, scored {res.level}")
        if problems:
            issues.append({"category": cid, "problems": problems})
            text = template_rationale(_facts(res))
        fixed[cid] = text
    return {**s, "rationales": fixed, "verification_issues": issues}


def _review(s):
    org = s["org"]
    reviews = read_reviews(org.dir / "reviews.yaml")
    log = read_log(org.dir / "audit-log.jsonl")
    statuses = apply_reviews(s["results"], s["evidence_by_id"], reviews, org.assessor, log)
    return {**s, "statuses": statuses, "review_queue": queue(statuses), "audit_problems": verify_audit_log(org.dir / "audit-log.jsonl")}


def _rollup(s):
    levels = {cid: st["final_level"] for cid, st in s["statuses"].items()}
    pillars = pillar_rollup(levels, s["org"].critical)
    return {**s, "pillars": pillars, "overall": overall(pillars)}


def _gaps(s):
    return {**s, "gaps": gap_analysis(s["results"], s["statuses"], s["org"].target)}


def _roadmap(s):
    items = work_items(s["gaps"])
    return {**s, "items": items, "schedule": schedule(items, s["org"].config.get("capacity", 4))}


def build_graph():
    g = StateGraph()
    for name, fn in zip(NODES, [_load, _collect, _score, _explain, _verify, _review, _rollup, _gaps, _roadmap], strict=True):
        g.add_node(name, fn)
    for a, b in itertools.pairwise(NODES):
        g.add_edge(a, b)
    g.add_edge("roadmap", END)
    return g.compile(entry="load", max_steps=len(NODES) + 2)


def assess(org_id: str, live: bool = False, root: Path | None = None, llm: MockLLM | None = None, evidence=None) -> dict[str, Any]:
    state = build_graph().invoke({"org_id": org_id, "live": live, "root": root, "llm": llm or MockLLM(), "evidence_override": evidence})
    state["final"] = not state["review_queue"] and not state["audit_problems"]
    return state


def summary(state: dict[str, Any]) -> dict[str, Any]:
    """JSON-friendly view of an assessment (what the CLI, MCP server and report use)."""
    org = state["org"]
    cats = []
    for cid, r in state["results"].items():
        st = state["statuses"][cid]
        cats.append(
            {
                "id": cid,
                "name": r.name,
                "pillar": r.pillar,
                "critical": r.critical,
                "computed_level": r.level,
                "level": st["final_level"],
                "confidence": r.confidence,
                "status": st["status"],
                "evidence": r.evidence,
                "rationale": state["rationales"][cid],
                "next_missing": r.next_missing,
                "target": org.target(cid),
            }
        )
    return {
        "org": org.id,
        "name": org.name,
        "kind": org.config.get("kind", ""),
        "assessor": org.assessor,
        "overall": state["overall"],
        "pillars": state["pillars"],
        "categories": cats,
        "review_queue": state["review_queue"],
        "final": state["final"],
        "audit_problems": state["audit_problems"],
        "verification_issues": state["verification_issues"],
        "evidence_count": len(state["evidence"]),
        "sources": org.repo_names(),
        "questionnaire_label": (org.answers() or {}).get("label"),
    }
