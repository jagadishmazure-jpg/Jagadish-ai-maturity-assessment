"""Load the maturity model (dimensions, capabilities, levels) and the rubric (signals, criteria per level)."""

from __future__ import annotations

from functools import cache
from typing import Any

import yaml

from aimaturity import FRAMEWORK, RUBRIC

LEVEL_NAMES = {1: "Explore", 2: "Prove", 3: "Operate", 4: "Scale", 5: "Optimise"}
LEVELS = tuple(LEVEL_NAMES)  # 1..5
TOP = LEVELS[-1]
STEPS = LEVELS[1:]  # levels that need evidence: 2..5


@cache
def framework() -> dict[str, Any]:
    return yaml.safe_load((FRAMEWORK / "framework.yaml").read_text())


@cache
def rubric() -> dict[str, Any]:
    return yaml.safe_load((RUBRIC / "capabilities.yaml").read_text())


@cache
def signals() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in yaml.safe_load((RUBRIC / "signals.yaml").read_text())["signals"]}


@cache
def questions() -> dict[str, dict[str, Any]]:
    return {q["id"]: q for q in yaml.safe_load((RUBRIC / "questionnaire.yaml").read_text())["questions"]}


def dimensions() -> list[dict[str, Any]]:
    return framework()["dimensions"]


def dimension_weights() -> dict[str, float]:
    return {d["id"]: float(d["weight"]) for d in dimensions()}


def criteria(capability_id: str, level: int) -> list[str]:
    """All criteria (must first, then support) for one level of one capability."""
    lv = rubric()["capabilities"][capability_id]["levels"][level]
    return [*lv["must"], *lv["support"]]


def capabilities() -> dict[str, dict[str, Any]]:
    """capability id -> capability dict with its dimension and rubric entry merged in."""
    out = {}
    r = rubric()
    for d in dimensions():
        for c in d["capabilities"]:
            out[c["id"]] = {
                **c,
                "dimension": d["id"],
                "dimension_name": d["name"],
                "rubric": r["capabilities"][c["id"]],
                "anchor": c["id"] in r["anchors"],
            }
    return out


def dimension_of(capability_id: str) -> str:
    return capabilities()[capability_id]["dimension"]


def is_question(signal_id: str) -> bool:
    return signal_id.startswith("q_")


def capability_signals(capability_id: str) -> list[str]:
    seen: list[str] = []
    for lvl in STEPS:
        for s in criteria(capability_id, lvl):
            if s not in seen:
                seen.append(s)
    return seen


def check_consistency() -> list[str]:
    """Problems that would make scoring meaningless; the test suite requires an empty list."""
    errs: list[str] = []
    caps = capabilities()
    sig, qs = signals(), questions()
    r = rubric()
    if sorted(framework()["levels"]) != list(LEVELS):
        errs.append(f"expected levels {list(LEVELS)}, found {sorted(framework()['levels'])}")
    if len(dimensions()) != 8:
        errs.append(f"expected 8 dimensions, found {len(dimensions())}")
    if abs(sum(dimension_weights().values()) - 1.0) > 1e-9:
        errs.append(f"dimension weights sum to {sum(dimension_weights().values())}, not 1.0")
    if set(r["capabilities"]) != set(caps):
        errs.append("rubric and framework list different capabilities")
    for a in r["anchors"]:
        if a not in caps:
            errs.append(f"unknown anchor {a}")
    for d in dimensions():
        if not any(c["id"] in r["anchors"] for c in d["capabilities"]):
            errs.append(f"dimension {d['id']} has no anchor capability")
    for cid, c in caps.items():
        levels = c["rubric"]["levels"]
        if sorted(levels) != list(STEPS):
            errs.append(f"{cid}: rubric must define levels {list(STEPS)}")
            continue
        for lvl in STEPS:
            if not levels[lvl]["must"]:
                errs.append(f"{cid} level {lvl}: needs at least one must criterion")
            for s in criteria(cid, lvl):
                if is_question(s):
                    if s not in qs:
                        errs.append(f"{cid} level {lvl}: unknown question {s}")
                elif s not in sig:
                    errs.append(f"{cid} level {lvl}: unknown signal {s}")
            if lvl >= r["ceiling_from"] and all(is_question(s) for s in levels[lvl]["must"]):
                errs.append(f"{cid} level {lvl}: evidence ceiling needs an artifact among the must criteria")
        for d in c["rubric"]["depends_on"]:
            if d not in caps:
                errs.append(f"{cid}: unknown dependency {d}")
        for k in ("nist_ai_rmf", "iso_42001", "eu_ai_act"):
            if k not in c.get("maps_to", {}):
                errs.append(f"{cid}: crosswalk misses {k}")
    used = {s for c in caps for s in capability_signals(c)}
    errs += [f"signal {s} is not used by any capability" for s in sig if s not in used]
    errs += [f"question {q} is not used by any capability" for q in qs if q not in used]
    errs += [f"question {q} names unknown capability {v['capability']}" for q, v in qs.items() if v["capability"] not in caps]
    return errs
