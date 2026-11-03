# Component: prioritised Month 1-12 roadmap

Gap steps become work items with priorities and dependencies, then a scheduler places them in Months
1 to 12 under a capacity limit. Quick wins come first; what does not fit goes to a backlog. There are no
calendar dates, only month numbers.

Sections: [1. Purpose](#1-purpose) · [2. Architecture](#2-architecture) · [3. How it works](#3-how-it-works) · [4. Key files](#4-key-files) · [5. Code excerpts](#5-code-excerpts) · [6. Configuration](#6-configuration) · [7. Commands](#7-commands) · [8. Real output](#8-real-output) · [9. Tests and gates](#9-tests-and-gates) · [10. Guardrails](#10-guardrails) · [11. Security and governance](#11-security-and-governance) · [12. Observability](#12-observability) · [13. Failure modes](#13-failure-modes) · [14. Mapping to Azure services](#14-mapping-to-azure-services) · [15. Limitations](#15-limitations) · [16. Interview talking points](#16-interview-talking-points) · [17. Adopt this](#17-adopt-this)

## 1. Purpose

* Give leaders an order of work that respects dependencies and capacity, with early visible wins.

## 2. Architecture

```mermaid
flowchart TB
  G[gap steps] --> W[work items: capability->level]
  D[depends_on in rubric] --> W
  W --> P[priority = 10 gap + 5 anchor + 2 unblocks + 3 (1 - confidence) + 20 weight]
  P --> K{quick win?<br/>first step, effort S, no waits}
  K --> S[scheduler: months 1-12, capacity N]
  S --> PL[plan with start/end months]
  S --> B[backlog beyond Month 12]
  S --> MS[re-assess at Month 6 and 12]
```

## 3. How it works

1. Each step is an item `c->L`, for example `AE-1->3`. It waits on `c->L-1` and on steps of the capabilities `c` depends on up to level L-1.
2. Priority = 10 x gap + 5 if anchor + 2 x items waiting on it + 3 x (1 - confidence) + 20 x dimension weight, so large gaps, anchors, unblockers, uncertain scores and heavier dimensions come first.
3. Quick wins: first step of a capability, effort S, nothing to wait for; they must start in Months 1-3.
4. The scheduler walks months 1-12, starting ready items by quick-win first, then priority, while fewer than `capacity` are in flight.
5. Effort S/M/L lasts 1/2/3 months; items that cannot finish by Month 12 go to the backlog.
6. Milestones: re-assess in Month 6 and Month 12.

## 4. Key files

| File | Role |
|---|---|
| `src/aimaturity/roadmap.py` | work_items, schedule, months_view |
| `rubric/capabilities.yaml` | Effort and dependencies |
| `framework/framework.yaml` | Dimension weights used in priority |
| `samples/*/org.yaml` | `capacity` |

## 5. Code excerpts

<!-- code: src/aimaturity/roadmap.py::work_items -->
```python
def work_items(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cats = capabilities()
    weight = dimension_weights()
    items: dict[str, dict[str, Any]] = {}
    by_cat = {g["capability"]: g for g in gaps}
    for g in gaps:
        for n, step in enumerate(g["steps"]):
            iid = f"{g['capability']}->{step['to_level']}"
            deps = [f"{g['capability']}->{step['to_level'] - 1}"] if n else []
            for d in cats[g["capability"]]["rubric"]["depends_on"]:
                deps += [f"{d}->{s['to_level']}" for s in by_cat[d]["steps"] if s["to_level"] <= step["to_level"] - 1]
            items[iid] = {
                "id": iid,
                "capability": g["capability"],
                "name": g["name"],
                "dimension": g["dimension"],
                "to_level": step["to_level"],
                "effort": step["effort"],
                "months": DURATION[step["effort"]],
                "depends_on": deps,
                "anchor": g["anchor"],
                "weight": weight[g["dimension"]],
                "gap": g["gap"],
                "confidence": g["confidence"],
                "action": step["action"],
                "missing": step["missing"],
            }
    for it in items.values():
        it["unblocks"] = sorted(o["id"] for o in items.values() if it["id"] in o["depends_on"])
        it["priority"] = round(10 * it["gap"] + 5 * it["anchor"] + 2 * len(it["unblocks"]) + 3 * (1 - it["confidence"]) + 20 * it["weight"], 2)
        first = not any(d.startswith(it["capability"] + "->") for d in it["depends_on"])
        it["kind"] = "quick-win" if first and it["effort"] == "S" and not it["depends_on"] else "strategic"
    return sorted(items.values(), key=lambda i: (-i["priority"], i["id"]))
```
<!-- /code -->

<!-- code: src/aimaturity/roadmap.py::schedule -->
```python
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
        "capacity": capacity,
        "plan": plan,
        "backlog": sorted((p["id"] for p in pending), key=_item_order),
        "milestones": [
            {"month": 6, "what": "Re-assess all capabilities and refresh the plan"},
            {"month": 12, "what": "Full re-assessment and target reset"},
        ],
    }
```
<!-- /code -->

## 6. Configuration

| Setting | Where | Default |
|---|---|---|
| capacity | `org.yaml` | 4 |
| durations | `roadmap.DURATION` | S=1, M=2, L=3 |
| horizon | `roadmap.MONTHS` | 12 |

## 7. Commands

```bash
aimaturity roadmap --org kestrel-bay-bank
aimaturity roadmap --org portfolio
```

## 8. Real output

<!-- output: roadmap --org kestrel-bay-bank -->
```text
step     kind       months  effort  priority  waits on
-------  ---------  ------  ------  --------  --------
PL-1->3  strategic  1-2     M       17.14     -
PO-2->3  strategic  1-2     M       13.32     -
DF-1->3  strategic  1-2     M       13.11     -
PO-3->3  strategic  1-2     M       13.02     -
AE-1->4  strategic  3-4     M       17.86     PL-1->3
AE-2->3  strategic  3-4     M       12.92     -
FC-2->3  strategic  3-4     M       12.87     -
SI-3->4  strategic  3-4     M       12.86     PL-1->3

Month  1: PL-1->3, PO-2->3, DF-1->3, PO-3->3
Month  2: PL-1->3, PO-2->3, DF-1->3, PO-3->3
Month  3: AE-1->4, AE-2->3, FC-2->3, SI-3->4
Month  4: AE-1->4, AE-2->3, FC-2->3, SI-3->4
Month  5: -
Month  6: -
Month  7: -
Month  8: -
Month  9: -
Month 10: -
Month 11: -
Month 12: -
backlog: none
```
<!-- /output -->

## 9. Tests and gates

* `tests/test_gaps_roadmap.py`: dependencies finish before dependants start, capacity respected, quick wins by Month 3, durations, every item planned or backlogged, milestones.

## 10. Guardrails

* No dates anywhere: months are relative to the start of the programme.
* The plan is advice; humans own the commitments.

## 11. Security and governance

Runs offline with no credentials. Reads repositories through `git ls-files` and never executes their code; evidence holds paths and short match details, never file contents or secrets.

## 12. Observability

The report includes the plan table and a month-by-month view of items in flight.

## 13. Failure modes

| Failure | Behaviour |
|---|---|
| Too much work for capacity | backlog grows; raise capacity or lower targets |
| Circular dependencies | prevented by a test on the rubric |

## 14. Mapping to Azure services

* **Azure DevOps Delivery Plans** or **GitHub Projects** can display the months as iterations.
* **Microsoft Foundry**: a hosted model replaces `MockLLM` for rationales, and Foundry evaluations score rationale groundedness against the cited evidence.
* **Microsoft Purview**: register the evidence store and reports as data assets with lineage back to the scanned repositories, and keep questionnaire answers under a sensitivity label.
* **Azure Policy**: audit that the evidence store stays keyless and versioned and that the Key Vault keeps RBAC, so the controls the assessment relies on cannot drift silently.
* **Azure Monitor / Log Analytics**: job logs, blob access logs and Key Vault audit events land in one workspace, where a query can trend maturity runs over time.

## 15. Limitations

* Greedy scheduling is simple and explainable, not optimal.
* Effort sizes are per capability level, not per organisation.

## 16. Interview talking points

* "Quick wins are defined in code: first step, small, nothing to wait for. Everything else is strategic."

## 17. Adopt this

1. Set `capacity:` to the number of improvement streams you can run at once.
2. Adjust effort and `depends_on` in `rubric/capabilities.yaml`.
3. Change the priority formula in `work_items` and check the plan with `aimaturity roadmap`.
