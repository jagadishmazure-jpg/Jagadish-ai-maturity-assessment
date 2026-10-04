"""``aimaturity`` command line. Everything is offline; only ``review``, ``report`` and
``collect --write`` write files, and only inside this repository.

aimaturity framework [--pillar P1] | category ID | orgs | validate
aimaturity collect --org ORG [--live] [--write] | assess --org ORG [--json] [--live]
aimaturity explain --org ORG --category ID | gaps --org ORG | roadmap --org ORG | links --org ORG
aimaturity queue --org ORG | review --org ORG --category ID --reviewer NAME --decision confirm|override [--level N] --comment TEXT
aimaturity audit --org ORG | report (--org ORG | --all) [--check] | evals [--json] | agent-card | mcp | mcp-demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from typing import Any

from aimaturity import ROOT


def _p(text: str = "") -> None:
    print(text)


def table(rows: list[dict[str, Any]], keys: list[str], heads: list[str] | None = None) -> str:
    heads = heads or keys
    cells = [[str(r.get(k, "")) for k in keys] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) if cells else len(h) for i, h in enumerate(heads)]
    line = lambda vals: "  ".join(v.ljust(w) for v, w in zip(vals, widths, strict=True)).rstrip()  # noqa: E731
    return "\n".join([line(heads), line(["-" * w for w in widths]), *(line(c) for c in cells)])


def cmd_framework(a) -> int:
    from aimaturity.framework import LEVEL_NAMES, categories, pillars

    if not a.pillar:
        _p("Levels: " + ", ".join(f"{k} {v}" for k, v in LEVEL_NAMES.items()))
        _p(
            table(
                [{"id": p["id"], "name": p["name"], "n": len(p["categories"])} for p in pillars()],
                ["id", "name", "n"],
                ["pillar", "name", "categories"],
            )
        )
        _p(f"\n{len(categories())} categories; critical by default: {', '.join(c for c, v in categories().items() if v['critical'])}")
        return 0
    rows = [{"id": c["id"], "name": c["name"], "critical": "yes" if c["critical"] else ""} for c in categories().values() if c["pillar"] == a.pillar]
    _p(table(rows, ["id", "name", "critical"], ["category", "name", "critical"]))
    return 0


def cmd_category(a) -> int:
    from aimaturity.framework import LEVEL_NAMES, categories
    from aimaturity.gaps import describe

    c = categories()[a.category_id]
    _p(f"{c['id']} {c['name']} ({c['pillar']} {c['pillar_name']}){' - critical' if c['critical'] else ''}")
    _p(c["summary"])
    for lvl in (1, 2, 3, 4):
        _p(f"  {lvl} {LEVEL_NAMES[lvl]}: {c['descriptors'][lvl]}")
    for lvl in (2, 3, 4):
        _p(f"  evidence for {lvl}: " + "; ".join(f"{s} ({describe(s)})" for s in c["rubric"]["levels"][lvl]))
    return 0


def cmd_orgs(a) -> int:
    from aimaturity.orgs import list_orgs, load_org

    rows = []
    for o in list_orgs():
        org = load_org(o)
        mode = "manifest" if org.config.get("manifest") else "repos+snapshot"
        rows.append({"id": o, "name": org.name, "mode": mode, "repos": len(org.repo_names()), "answers": (org.answers() or {}).get("label", "-")})
    _p(table(rows, ["id", "name", "mode", "repos", "answers"], ["org", "name", "evidence", "repos", "questionnaire"]))
    return 0


def cmd_validate(a) -> int:
    from aimaturity.validate import validate_all

    errs = validate_all()
    _p("\n".join(errs) if errs else "framework, rubric, schemas and sample orgs: OK")
    return 1 if errs else 0


def cmd_collect(a) -> int:
    from aimaturity.orgs import gather, live_sources, load_org, scan, write_snapshot

    org = load_org(a.org)
    if a.write:
        if not a.live:
            _p("--write needs --live (it refreshes the snapshot from the checkouts)")
            return 2
        items = scan(live_sources(org))
        _p(f"wrote {write_snapshot(org, items).relative_to(ROOT)} ({len(items)} artifact items)")
        return 0
    ev = gather(org, live=a.live)
    by = Counter((e.source, e.collector) for e in ev)
    rows = [{"source": s, "collector": c, "items": n} for (s, c), n in sorted(by.items())]
    _p(table(rows, ["source", "collector", "items"]))
    _p(f"\n{len(ev)} evidence items, {len({e.signal for e in ev})} distinct signals")
    return 0


def _state(a):
    from aimaturity.agents.assessor import assess

    return assess(a.org, live=getattr(a, "live", False))


def cmd_assess(a) -> int:
    from aimaturity.agents.assessor import summary

    s = summary(_state(a))
    if a.json:
        _p(json.dumps(s, indent=1))
        return 0
    _p(f"{s['name']}: overall Level {s['overall']['level']} ({s['overall']['level_name']}), mean {s['overall']['mean']}")
    _p(
        table(
            [{**p, "capped_by": ",".join(p["capped_by"]) or "-"} for p in s["pillars"]],
            ["id", "name", "level", "level_name", "mean", "capped_by"],
            ["pillar", "name", "level", "", "mean", "capped by"],
        )
    )
    _p("")
    _p(
        table(
            s["categories"],
            ["id", "level", "computed_level", "confidence", "status", "target"],
            ["cat", "level", "computed", "conf", "status", "target"],
        )
    )
    _p(f"\nreview queue: {', '.join(s['review_queue']) or 'empty'}; final: {s['final']}")
    return 0


def cmd_explain(a) -> int:
    st = _state(a)
    r = st["results"][a.category]
    _p(f"{r.id} {r.name}: level {r.level} ({r.level_name}), confidence {r.confidence:.2f}, status {st['statuses'][r.id]['status']}")
    _p(f"rationale: {st['rationales'][r.id]}")
    for sid, ss in r.signals.items():
        mark = "x" if ss.present == 1 else ("~" if ss.present else " ")
        _p(f"  [{mark}] {sid:<28} {ss.basis:<16} {', '.join(ss.evidence[:3])}")
    for i in r.evidence[:8]:
        e = st["evidence_by_id"][i]
        _p(f"  {i} {e.source}:{e.path} ({e.detail})")
    if r.review_reasons:
        _p("needs review: " + "; ".join(r.review_reasons))
    return 0


def cmd_gaps(a) -> int:
    st = _state(a)
    rows = [{**g, "first": g["steps"][0]["action"][:70]} for g in sorted(st["gaps"], key=lambda g: (-g["gap"], g["category"])) if g["gap"]]
    _p(table(rows, ["category", "current", "target", "gap", "first"], ["cat", "now", "target", "gap", "first action"]))
    return 0


def cmd_roadmap(a) -> int:
    from aimaturity.roadmap import months_view

    st = _state(a)
    sch = st["schedule"]
    _p(
        table(
            [{**p, "months": f"{p['start']}-{p['end']}", "deps": ",".join(p["depends_on"]) or "-"} for p in sch["plan"]],
            ["id", "kind", "months", "effort", "priority", "deps"],
            ["step", "kind", "months", "effort", "priority", "waits on"],
        )
    )
    view = months_view(sch)
    _p("")
    for m, ids in view.items():
        _p(f"Month {m:>2}: {', '.join(ids) or '-'}")
    _p(f"backlog: {', '.join(sch['backlog']) or 'none'}")
    return 0


def cmd_links(a) -> int:
    from aimaturity.crosslinks import check_links

    rows = check_links(_state(a))
    _p(table(rows, ["repo", "category", "cited", "ok"]) if rows else "no cross-links configured")
    return 0 if all(r["ok"] for r in rows) else 1


def cmd_queue(a) -> int:
    st = _state(a)
    rows = [
        {"category": c, "name": st["results"][c].name, "why": "; ".join(st["results"][c].review_reasons) or "evidence changed since review"}
        for c in st["review_queue"]
    ]
    _p(table(rows, ["category", "name", "why"]) if rows else "review queue is empty")
    return 0


def cmd_review(a) -> int:
    from aimaturity.hitl import ReviewError, record_review

    st = _state(a)
    org = st["org"]
    try:
        r = record_review(
            org.dir / "reviews.yaml",
            org.dir / "audit-log.jsonl",
            org.assessor,
            st["results"],
            st["evidence_by_id"],
            category=a.category,
            reviewer=a.reviewer,
            decision=a.decision,
            level=a.level,
            comment=a.comment,
        )
    except ReviewError as e:
        _p(f"rejected: {e}")
        return 1
    _p(f"recorded {r['decision']} for {r['category']} at level {r['level']} (audit {r['audit_hash'][:12]})")
    return 0


def cmd_audit(a) -> int:
    from aimaturity.hitl import read_log, verify_audit_log
    from aimaturity.orgs import load_org

    org = load_org(a.org)
    log = org.dir / "audit-log.jsonl"
    problems = verify_audit_log(log)
    _p(f"{len(read_log(log))} entries; chain {'intact' if not problems else 'BROKEN'}")
    for p in problems:
        _p(f"  {p}")
    return 1 if problems else 0


def cmd_report(a) -> int:
    from aimaturity.agents.assessor import assess
    from aimaturity.orgs import list_orgs
    from aimaturity.report import write

    orgs = list_orgs() if a.all else [a.org]
    bad = 0
    for o in orgs:
        drift = write(assess(o), check=a.check)
        if a.check:
            _p(f"{o}: {'up to date' if not drift else 'DRIFT in ' + ', '.join(drift)}")
            bad += bool(drift)
        else:
            _p(f"{o}: wrote samples/{o}/report/report.md, report.html, radar.svg")
    return 1 if bad else 0


def cmd_evals(a) -> int:
    from aimaturity.evals import run_all

    res = run_all()
    if a.json:
        _p(json.dumps(res, indent=1))
    else:
        for r in res:
            facts = ", ".join(f"{k}={v}" for k, v in r.items() if k not in {"gate", "ok", "by_source"})
            _p(f"{'PASS' if r['ok'] else 'FAIL'}  {r['gate']:<12} {facts}")
    return 0 if all(r["ok"] for r in res) else 1


def cmd_agent_card(a) -> int:
    _p((ROOT / "a2a" / "agent-card.json").read_text().rstrip())
    return 0


def cmd_mcp(a) -> int:
    from aimaturity.mcp_server import build_server

    build_server().run()
    return 0


def cmd_mcp_demo(a) -> int:
    from aimaturity.mcp_server import demo

    for line in asyncio.run(demo()):
        _p(line)
    return 0


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="aimaturity", description="Evidence-based AI maturity assessment (offline).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def org(p, required=True):
        p.add_argument("--org", required=required)
        return p

    p = sub.add_parser("framework")
    p.add_argument("--pillar")
    p.set_defaults(fn=cmd_framework)
    p = sub.add_parser("category")
    p.add_argument("category_id")
    p.set_defaults(fn=cmd_category)
    sub.add_parser("orgs").set_defaults(fn=cmd_orgs)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    p = org(sub.add_parser("collect"))
    p.add_argument("--live", action="store_true")
    p.add_argument("--write", action="store_true")
    p.set_defaults(fn=cmd_collect)
    p = org(sub.add_parser("assess"))
    p.add_argument("--json", action="store_true")
    p.add_argument("--live", action="store_true")
    p.set_defaults(fn=cmd_assess)
    p = org(sub.add_parser("explain"))
    p.add_argument("--category", required=True)
    p.set_defaults(fn=cmd_explain)
    for name, fn in [("gaps", cmd_gaps), ("roadmap", cmd_roadmap), ("links", cmd_links), ("queue", cmd_queue), ("audit", cmd_audit)]:
        org(sub.add_parser(name)).set_defaults(fn=fn)
    p = org(sub.add_parser("review"))
    p.add_argument("--category", required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--decision", choices=["confirm", "override"], required=True)
    p.add_argument("--level", type=int)
    p.add_argument("--comment", required=True)
    p.set_defaults(fn=cmd_review)
    p = org(sub.add_parser("report"), required=False)
    p.add_argument("--all", action="store_true")
    p.add_argument("--check", action="store_true")
    p.set_defaults(fn=cmd_report)
    p = sub.add_parser("evals")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_evals)
    sub.add_parser("agent-card").set_defaults(fn=cmd_agent_card)
    sub.add_parser("mcp").set_defaults(fn=cmd_mcp)
    sub.add_parser("mcp-demo").set_defaults(fn=cmd_mcp_demo)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    if a.cmd == "report" and not (a.all or a.org):
        _p("report needs --org ORG or --all")
        return 2
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
