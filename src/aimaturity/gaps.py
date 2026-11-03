"""Gap analysis: where each capability is, where the organisation wants it, and what is missing.

The target defaults to level 3 (Operate) and can be set per dimension or capability in ``org.yaml``.
Each missing level becomes one step with the criteria still absent (must criteria first) and the framework's suggested
actions for that level.
"""

from __future__ import annotations

from typing import Any

from aimaturity.framework import LEVEL_NAMES, capabilities, criteria, is_question, questions, signals


def describe(signal_id: str) -> str:
    return questions()[signal_id]["text"] if is_question(signal_id) else signals()[signal_id]["description"]


def gap_analysis(results, statuses, target_of) -> list[dict[str, Any]]:
    cats = capabilities()
    rows = []
    for cid, res in results.items():
        current = statuses[cid]["final_level"]
        target = target_of(cid)
        steps = []
        for lvl in range(current + 1, target + 1):
            missing = [s for s in criteria(cid, lvl) if res.signals[s].present < 1]
            must = cats[cid]["rubric"]["levels"][lvl]["must"]
            steps.append(
                {
                    "to_level": lvl,
                    "level_name": LEVEL_NAMES[lvl],
                    "missing": missing,
                    "missing_must": [s for s in missing if s in must],
                    "missing_text": [describe(s) for s in missing],
                    "action": cats[cid]["actions"].get(lvl, ""),
                    "effort": cats[cid]["rubric"]["effort"][lvl],
                }
            )
        rows.append(
            {
                "capability": cid,
                "name": res.name,
                "dimension": res.dimension,
                "anchor": res.anchor,
                "current": current,
                "target": target,
                "gap": max(0, target - current),
                "confidence": res.confidence,
                "status": statuses[cid]["status"],
                "steps": steps,
            }
        )
    return rows
