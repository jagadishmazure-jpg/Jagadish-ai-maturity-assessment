"""Turn gaps into a prioritised, dependency-aware Month 1-12 plan (no calendar dates).

* One work item per missing level step: ``2.3->3`` means "lift category 2.3 to level 3".
* Dependencies: the previous step of the same category, and for every category it depends on
  (rubric ``depends_on``) any step of that category to a level at most one below.
* Priority = 10 x gap + 6 if critical + 2 x number of items waiting on it + 3 x (1 - confidence).
* Quick win: the first step of a category, effort S, with nothing it waits on.
* Scheduling: months 1-12, at most ``capacity`` items in flight; quick wins start first and must
  start in Months 1-3. Effort S/M/L lasts 1/2/3 months. What does not fit goes to the backlog.
* Re-assessment milestones in Month 6 and Month 12.
"""

from __future__ import annotations

from typing import Any

from aimaturity.framework import categories

DURATION = {"S": 1, "M": 2, "L": 3}
MONTHS = 12


def work_items(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cats = categories()
    items: dict[str, dict[str, Any]] = {}
    by_cat = {g["category"]: g for g in gaps}
    for g in gaps:
        for n, step in enumerate(g["steps"]):
            iid = f"{g['category']}->{step['to_level']}"
            deps = [f"{g['category']}->{step['to_level'] - 1}"] if n else []
            for d in cats[g["category"]]["rubric"]["depends_on"]:
                deps += [f"{d}->{s['to_level']}" for s in by_cat[d]["steps"] if s["to_level"] <= step["to_level"] - 1]
            items[iid] = {
                "id": iid, "category": g["category"], "name": g["name"], "pillar": g["pillar"], "to_level": step["to_level"],
                "effort": step["effort"], "months": DURATION[step["effort"]], "depends_on": deps, "critical": g["critical"],
                "gap": g["gap"], "confidence": g["confidence"], "action": step["action"], "missing": step["missing"],
            }
    for it in items.values():
        it["unblocks"] = sorted(o["id"] for o in items.values() if it["id"] in o["depends_on"])
        it["priority"] = round(10 * it["gap"] + 6 * it["critical"] + 2 * len(it["unblocks"]) + 3 * (1 - it["confidence"]), 2)
        first = not any(d.startswith(it["category"] + "->") for d in it["depends_on"])
        it["kind"] = "quick-win" if first and it["effort"] == "S" and not it["depends_on"] else "strategic"
    return sorted(items.values(), key=lambda i: (-i["priority"], i["id"]))


def schedule(items: list[dict[str, Any]], capacity: int = 4) -> dict[str, Any]:
    done_at: dict[str, int] = {}  # item id -> month it finishes (inclusive)
    running: list[tuple[str, int]] = []
    plan: list[dict[str, Any]] = []
    pending = list(items)
    for month in range(1, MONTHS + 1):
        running = [(i, end) for i, end in running if end >= month]
        ready = [it for it in pending if all(d in done_at and done_at[d] < month for d in it["depends_on"])]
        ready.sort(key=lambda it: (it["kind"] != "quick-win", -it["priority"], it["id"]))
        for it in ready:
            if len(running) >= capacity:
                break
            if it["kind"] == "quick-win" and month > 3:
                continue
            end = month + it["months"] - 1
            if end > MONTHS:
                continue
            running.append((it["id"], end))
            done_at[it["id"]] = end
            plan.append({**it, "start": month, "end": end})
            pending.remove(it)
    plan.sort(key=lambda p: (p["start"], -p["priority"], p["id"]))
    return {
        "capacity": capacity, "plan": plan, "backlog": sorted((p["id"] for p in pending), key=lambda i: [float(x) for x in i.replace("->", ".").split(".")]),
        "milestones": [{"month": 6, "what": "Re-assess all categories and refresh the plan"}, {"month": 12, "what": "Full re-assessment and target reset"}],
    }


def months_view(sched: dict[str, Any]) -> dict[int, list[str]]:
    view: dict[int, list[str]] = {m: [] for m in range(1, MONTHS + 1)}
    for p in sched["plan"]:
        for m in range(p["start"], p["end"] + 1):
            view[m].append(p["id"])
    return view
