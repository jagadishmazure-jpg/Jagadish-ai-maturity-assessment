"""Roll capability levels up to dimensions, an overall level and the Agentic Readiness Index.

* Dimension level = floor(mean of its capability levels), capped at (weakest anchor capability + 1):
  an anchor is the capability the rest of the dimension stands on. Anchors are configurable per
  organisation; defaults in rubric/capabilities.yaml.
* Overall level = floor(weighted mean of dimension levels, using the dimension weights in
  framework/framework.yaml), capped at (weakest dimension + 1) so one weak dimension cannot hide.
* Agentic Readiness Index (0-100) = weighted mean of (dimension mean - 1) / 4, times 100, where the
  dimension mean is the unrounded mean of its capability levels. It moves before levels do, so it is
  the number to trend between assessments.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

from aimaturity.framework import LEVEL_NAMES, TOP, dimension_weights, dimensions


def dimension_rollup(levels: dict[str, int], anchors: list[str]) -> list[dict[str, Any]]:
    out = []
    w = dimension_weights()
    for d in dimensions():
        ids = [c["id"] for c in d["capabilities"]]
        vals = [levels[i] for i in ids]
        mean = statistics.mean(vals)
        raw = math.floor(mean)
        anc = [levels[i] for i in ids if i in anchors]
        cap = min(anc) + 1 if anc else TOP
        lvl = min(raw, cap)
        out.append(
            {
                "id": d["id"],
                "name": d["name"],
                "weight": w[d["id"]],
                "level": lvl,
                "level_name": LEVEL_NAMES[lvl],
                "mean": round(mean, 2),
                "capped_by": [i for i in ids if i in anchors and levels[i] + 1 < raw],
            }
        )
    return out


def readiness_index(dimension_rows: list[dict[str, Any]]) -> float:
    return round(100 * sum(d["weight"] * (d["mean"] - 1) / (TOP - 1) for d in dimension_rows), 1)


def overall(dimension_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lv = [d["level"] for d in dimension_rows]
    weighted = sum(d["weight"] * d["level"] for d in dimension_rows)
    raw = math.floor(round(weighted, 6))
    lvl = min(raw, min(lv) + 1)
    return {
        "level": lvl,
        "level_name": LEVEL_NAMES[lvl],
        "mean": round(sum(d["weight"] * d["mean"] for d in dimension_rows), 2),
        "index": readiness_index(dimension_rows),
        "capped": lvl < raw,
    }
