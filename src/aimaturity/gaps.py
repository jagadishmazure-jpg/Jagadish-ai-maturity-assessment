"""Gap analysis: where each category is, where the organisation wants it, and what is missing.

The target defaults to level 3 (Dynamic) and can be set per pillar or category in ``org.yaml``.
Each missing level becomes one step with the signals still absent and the framework's suggested
actions for that level.
"""

from __future__ import annotations

from typing import Any

from aimaturity.framework import LEVEL_NAMES, categories, is_question, questions, signals


def describe(signal_id: str) -> str:
    return questions()[signal_id]["text"] if is_question(signal_id) else signals()[signal_id]["description"]


def gap_analysis(results, statuses, target_of) -> list[dict[str, Any]]:
    cats = categories()
    rows = []
    for cid, res in results.items():
        current = statuses[cid]["final_level"]
        target = target_of(cid)
        steps = []
        for lvl in range(current + 1, target + 1):
            need = cats[cid]["rubric"]["levels"][lvl]
            missing = [s for s in need if res.signals[s].present < 1]
            steps.append(
                {
                    "to_level": lvl, "level_name": LEVEL_NAMES[lvl], "missing": missing, "missing_text": [describe(s) for s in missing],
                    "actions": cats[cid]["actions"].get(lvl, []), "effort": cats[cid]["rubric"]["effort"][lvl],
                }
            )
        rows.append(
            {
                "category": cid, "name": res.name, "pillar": res.pillar, "critical": res.critical, "current": current, "target": target,
                "gap": max(0, target - current), "confidence": res.confidence, "status": statuses[cid]["status"], "steps": steps,
            }
        )
    return rows
