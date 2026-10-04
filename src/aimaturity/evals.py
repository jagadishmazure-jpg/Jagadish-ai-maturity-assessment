"""Eval gates: scoring stability, evidence-citation completeness and calibration against labels.

    aimaturity evals          # table, exit 1 when a gate fails
    aimaturity evals --json   # machine-readable
"""

from __future__ import annotations

import random
from typing import Any

import yaml

from aimaturity import EVALS
from aimaturity.agents.assessor import assess
from aimaturity.agents.llm import MockLLM, cited_ids, claimed_level
from aimaturity.collectors import Evidence, collect_questionnaire, number
from aimaturity.framework import categories, is_question, rubric, signals
from aimaturity.orgs import ManifestSource, list_orgs, load_org, scan
from aimaturity.scoring import REVIEW_BELOW, score_all


def thresholds() -> dict[str, Any]:
    return yaml.safe_load((EVALS / "thresholds.yaml").read_text())


def _levels(results) -> dict[str, tuple[int, float]]:
    return {cid: (r.level, r.confidence) for cid, r in results.items()}


def _renumber(items: list[Evidence]) -> list[Evidence]:
    return number([Evidence(**{**e.as_dict(), "id": ""}) for e in items])


def stability(t: dict[str, Any]) -> dict[str, Any]:
    identical, max_change, max_cats, moves, runs, nonlocal_moves = True, 0, 0, 0, 0, 0
    for org_id in list_orgs():
        state = assess(org_id)
        base = _levels(state["results"])
        scanned = bool(state["org"].repo_names())
        for seed in range(t["shuffle_runs"]):
            ev = list(state["evidence"])
            random.Random(seed).shuffle(ev)
            if _levels(score_all(_renumber(ev), scanned)) != base:
                identical = False
        ev = state["evidence"]
        step = max(1, len(ev) // 60)  # at most about 60 dropout runs per org
        for i in range(0, len(ev), step):
            res = score_all(_renumber(ev[:i] + ev[i + 1 :]), scanned)
            moved = [c for c in base if res[c].level != base[c][0]]
            diffs = [abs(res[c].level - base[c][0]) for c in moved]
            # locality: only categories that use the removed item's signal may move
            nonlocal_moves += sum(ev[i].signal not in state["results"][c].signals for c in moved)
            runs += 1
            moves += len(diffs)
            max_cats = max(max_cats, len(diffs))
            max_change = max([max_change, *diffs])
    mean = round(moves / runs, 3)
    ok = (identical or not t["identical_required"]) and nonlocal_moves == 0 and max_cats <= t["dropout_max_categories"] and mean <= t["dropout_mean_categories"]
    return {"gate": "stability", "ok": ok, "shuffle_identical": identical, "dropout_runs": runs, "nonlocal_moves": nonlocal_moves,
            "max_categories_moved": max_cats, "mean_categories_moved": mean, "max_level_change_info": max_change}


def citations(t: dict[str, Any]) -> dict[str, Any]:
    need, have, cited_total, cited_valid, injected, caught = 0, 0, 0, 0, 0, 0
    for org_id in list_orgs():
        state = assess(org_id)
        ids = state["evidence_by_id"]
        for cid, r in state["results"].items():
            if r.level >= 2:
                need += 1
                have += bool(r.evidence)
            cites = cited_ids(state["rationales"][cid])
            cited_total += len(cites)
            cited_valid += sum(c in ids and c in r.evidence for c in cites)
        for knob in ({"hallucinate": True}, {"overclaim": True}):
            bad = assess(org_id, llm=MockLLM(**knob))
            flagged = {i["category"] for i in bad["verification_issues"]}
            targets = [c for c, r in bad["results"].items() if knob.get("hallucinate") or r.level < 4]
            injected += len(targets)
            caught += sum(c in flagged for c in targets)
            # after the verifier, the stored rationale must be clean again
            assert all(claimed_level(bad["rationales"][c]) == r.level for c, r in bad["results"].items())
    comp, valid, catch = have / need, cited_valid / max(cited_total, 1), caught / injected
    ok = comp >= t["completeness_min"] and valid >= t["valid_ids_min"] and catch >= t["verifier_catch_min"]
    return {"gate": "citations", "ok": ok, "completeness": round(comp, 3), "valid_ids": round(valid, 3), "verifier_catch": round(catch, 3),
            "categories_checked": need, "injected": injected}


def synthetic_org(rng: random.Random, n: int) -> tuple[list[Evidence], dict[str, int]]:
    """A synthetic org with known levels: signal examples for every level reached, plus noise."""
    R = rubric()["categories"]
    truth = {cid: rng.choice([1, 2, 2, 3, 3, 4]) for cid in categories()}
    files: dict[str, dict[str, str]] = {}
    answers: dict[str, str] = {}
    present: set[str] = set()
    for cid, lvl in truth.items():
        for lv in range(2, lvl + 1):
            present.update(R[cid]["levels"][lv])
    noisy = set(present)
    for cid, lvl in truth.items():
        if lvl >= 2 and rng.random() < 0.12:  # an artifact the collectors miss
            noisy.discard(rng.choice(R[cid]["levels"][lvl]))
        if lvl < 4 and rng.random() < 0.08:  # stray evidence of the next level
            noisy.add(rng.choice(R[cid]["levels"][lvl + 1]))
    for sid in sorted(noisy):
        if is_question(sid):
            answers[sid] = "yes"
            continue
        s = signals()[sid]
        repo = files.setdefault(f"synthetic-{n}-{s['collector']}", {})
        repo[s["example"]["path"]] = repo.get(s["example"]["path"], "") + s["example"]["content"]
    items = scan([ManifestSource(name, c) for name, c in sorted(files.items())])
    items += collect_questionnaire({"label": "self-reported", "answers": answers})
    return number(items), truth


def calibration(t: dict[str, Any]) -> dict[str, Any]:
    rows = []  # (computed, label, confidence)
    rng = random.Random(t["seed"])
    for n in range(t["synthetic_orgs"]):
        ev, truth = synthetic_org(rng, n)
        res = score_all(ev)
        rows += [(res[c].level, truth[c], res[c].confidence, "synthetic") for c in truth]
    for org_id in list_orgs():
        org = load_org(org_id)
        if not org.config.get("labels"):
            continue
        labels = yaml.safe_load((org.dir / org.config["labels"]).read_text())["labels"]
        state = assess(org_id)
        rows += [(state["results"][c].level, labels[c], state["results"][c].confidence, org_id) for c in labels]
    exact = sum(a == b for a, b, _, _ in rows) / len(rows)
    within = sum(abs(a - b) <= 1 for a, b, _, _ in rows) / len(rows)
    hi = [a == b for a, b, c, _ in rows if c >= REVIEW_BELOW]
    lo = [a == b for a, b, c, _ in rows if c < REVIEW_BELOW]
    hi_acc = sum(hi) / len(hi) if hi else 1.0
    lo_acc = sum(lo) / len(lo) if lo else 0.0
    ok = exact >= t["exact_min"] and within >= t["within_one_min"] and (hi_acc >= lo_acc or not t["high_conf_not_worse"])
    by_source = {}
    for _, _, _, src in rows:
        by_source[src] = by_source.get(src, 0) + 1
    return {"gate": "calibration", "ok": ok, "items": len(rows), "exact": round(exact, 3), "within_one": round(within, 3),
            "high_conf_accuracy": round(hi_acc, 3), "low_conf_accuracy": round(lo_acc, 3), "high_conf_items": len(hi), "by_source": by_source}


def run_all() -> list[dict[str, Any]]:
    t = thresholds()
    return [stability(t["stability"]), citations(t["citations"]), calibration(t["calibration"])]
