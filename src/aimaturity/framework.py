"""Load the framework model (pillars, categories, levels) and the rubric (signals, level mapping)."""

from __future__ import annotations

from functools import cache
from typing import Any

import yaml

from aimaturity import FRAMEWORK, RUBRIC

LEVEL_NAMES = {1: "Basic", 2: "Ready", 3: "Dynamic", 4: "Advanced"}


@cache
def framework() -> dict[str, Any]:
    return yaml.safe_load((FRAMEWORK / "framework.yaml").read_text())


@cache
def rubric() -> dict[str, Any]:
    return yaml.safe_load((RUBRIC / "categories.yaml").read_text())


@cache
def signals() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in yaml.safe_load((RUBRIC / "signals.yaml").read_text())["signals"]}


@cache
def questions() -> dict[str, dict[str, Any]]:
    return {q["id"]: q for q in yaml.safe_load((RUBRIC / "questionnaire.yaml").read_text())["questions"]}


def pillars() -> list[dict[str, Any]]:
    return framework()["pillars"]


def categories() -> dict[str, dict[str, Any]]:
    """category id -> category dict with its pillar id and rubric entry merged in."""
    out = {}
    r = rubric()
    for p in pillars():
        for c in p["categories"]:
            out[c["id"]] = {**c, "pillar": p["id"], "pillar_name": p["name"], "rubric": r["categories"][c["id"]], "critical": c["id"] in r["critical"]}
    return out


def pillar_of(category_id: str) -> str:
    return categories()[category_id]["pillar"]


def is_question(signal_id: str) -> bool:
    return signal_id.startswith("q_")


def category_signals(category_id: str) -> list[str]:
    seen: list[str] = []
    for lvl in (2, 3, 4):
        for s in rubric()["categories"][category_id]["levels"][lvl]:
            if s not in seen:
                seen.append(s)
    return seen


def check_consistency() -> list[str]:
    """Problems that would make scoring meaningless; the test suite requires an empty list."""
    errs: list[str] = []
    cats = categories()
    sig, qs = signals(), questions()
    if len(pillars()) != 6:
        errs.append(f"expected 6 pillars, found {len(pillars())}")
    if len(cats) != 29:
        errs.append(f"expected 29 categories, found {len(cats)}")
    for cid, c in cats.items():
        for lvl, ids in c["rubric"]["levels"].items():
            for s in ids:
                if is_question(s):
                    if s not in qs:
                        errs.append(f"{cid} level {lvl}: unknown question {s}")
                elif s not in sig:
                    errs.append(f"{cid} level {lvl}: unknown signal {s}")
        for d in c["rubric"]["depends_on"]:
            if d not in cats:
                errs.append(f"{cid}: unknown dependency {d}")
    used = {s for c in cats for s in category_signals(c)}
    errs += [f"signal {s} is not used by any category" for s in sig if s not in used]
    errs += [f"question {q} is not used by any category" for q in qs if q not in used]
    return errs
