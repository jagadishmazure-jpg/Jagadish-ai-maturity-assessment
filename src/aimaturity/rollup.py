"""Roll category levels up to pillars and an overall level.

* Pillar level = floor(median of its category levels), capped by the level of any critical category
  in that pillar (the critical list is configurable per organisation; defaults in rubric/categories.yaml).
* Overall level = floor(median of pillar levels), capped at (lowest pillar + 1) so one weak pillar
  cannot hide behind strong ones.
* Pillar and overall means are kept as floats for the radar chart and trend lines.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

from aimaturity.framework import LEVEL_NAMES, pillars


def pillar_rollup(levels: dict[str, int], critical: list[str]) -> list[dict[str, Any]]:
    out = []
    for p in pillars():
        ids = [c["id"] for c in p["categories"]]
        vals = [levels[i] for i in ids]
        median_level = math.floor(statistics.median(vals))
        crit = [levels[i] for i in ids if i in critical]
        cap = min(crit) if crit else 4
        lvl = min(median_level, cap)
        out.append(
            {
                "id": p["id"], "name": p["name"], "level": lvl, "level_name": LEVEL_NAMES[lvl], "mean": round(statistics.mean(vals), 2),
                "median": statistics.median(vals), "capped_by": [i for i in ids if i in critical and levels[i] < median_level],
            }
        )
    return out


def overall(pillar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lv = [p["level"] for p in pillar_rows]
    raw = math.floor(statistics.median(lv))
    lvl = min(raw, min(lv) + 1)
    return {"level": lvl, "level_name": LEVEL_NAMES[lvl], "mean": round(statistics.mean(p["mean"] for p in pillar_rows), 2), "capped": lvl < raw}
