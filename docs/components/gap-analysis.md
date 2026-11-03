# Component: gap analysis

For each capability, the gap is the target level minus the final level. Every missing level becomes a
step with the evidence still absent and the model's suggested action for that level.

Sections: [1. Purpose](#1-purpose) · [2. Architecture](#2-architecture) · [3. How it works](#3-how-it-works) · [4. Key files](#4-key-files) · [5. Code excerpts](#5-code-excerpts) · [6. Configuration](#6-configuration) · [7. Commands](#7-commands) · [8. Real output](#8-real-output) · [9. Tests and gates](#9-tests-and-gates) · [10. Guardrails](#10-guardrails) · [11. Security and governance](#11-security-and-governance) · [12. Observability](#12-observability) · [13. Failure modes](#13-failure-modes) · [14. Mapping to Azure services](#14-mapping-to-azure-services) · [15. Limitations](#15-limitations) · [16. Interview talking points](#16-interview-talking-points) · [17. Adopt this](#17-adopt-this)

## 1. Purpose

* Turn a score into a to-do list that names concrete evidence, not abstract advice.

## 2. Architecture

```mermaid
flowchart LR
  F[final level] --> G{target - final}
  T[targets: default 3,<br/>per dimension, per capability] --> G
  G --> S[steps per missing level]
  S --> M[missing signals + plain-language meaning]
  S --> A[suggested action, effort S/M/L]
```

## 3. How it works

1. `Org.target(capability)` reads capability, then dimension, then default targets from `org.yaml`.
2. For each level from final + 1 to target, the step lists missing signals (with their descriptions) and the action from `framework/framework.yaml`.
3. Effort comes from `rubric/capabilities.yaml` per step; must criteria are listed before support criteria, so the first missing item is the one that actually blocks the level.

## 4. Key files

| File | Role |
|---|---|
| `src/aimaturity/gaps.py` | gap_analysis, describe |
| `framework/framework.yaml` | Suggested actions per level |
| `samples/*/org.yaml` | Targets |

## 5. Code excerpts

<!-- code: src/aimaturity/gaps.py::gap_analysis -->
```python
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
```
<!-- /code -->

## 6. Configuration

| Target setting | Example |
|---|---|
| default | 3 (Operate) |
| dimensions | `{GR: 4}` raises all of Governance, Risk & Compliance |
| capabilities | `{FC-2: 2}` lowers one |

## 7. Commands

```bash
aimaturity gaps --org portfolio
aimaturity gaps --org valemont-revenue-agency
```

## 8. Real output

<!-- output: gaps --org valemont-revenue-agency -->
```text
capability  now  target  gap  first action
----------  ---  ------  ---  ----------------------------------------------------------------------
AE-1        1    3       2    Write an evaluation suite for the agent's main tasks.
FC-1        1    3       2    Provision budgets and caps as code.
GR-2        2    4       2    Score each risk in code with likelihood and impact.
PL-3        1    3       2    Instrument agents with OpenTelemetry or Application Insights.
SI-1        1    3       2    Turn on secret scanning and remove keys from code.
AE-2        2    3       1    Expose agent tools through an MCP server.
DF-2        2    3       1    Add automated quality tests that fail the load.
DF-3        2    3       1    Generate synthetic test data in code.
FC-2        1    2       1    Compute cost per task in code with tests.
PL-1        2    3       1    Move infrastructure to Bicep or Terraform and add a devcontainer.
PL-2        2    3       1    Add a protected production environment with required reviewers.
PO-1        2    3       1    Appoint an executive owner and charter a central team.
PO-2        2    3       1    Maintain role-based learning tracks with funded paths.
SI-2        2    3       1    Put an API gateway with content filtering in front of AI endpoints.
SV-1        2    3       1    Put a number on every outcome and publish the thesis.
SV-2        2    3       1    Publish a sequenced roadmap and make a business case mandatory for fun
SV-3        2    3       1    Compute value from usage data in code with tests.
```
<!-- /output -->

## 9. Tests and gates

* `tests/test_gaps_roadmap.py`: gap arithmetic, one step per missing level, actions and effort present, targets follow overrides.

## 10. Guardrails

* Gaps use final levels, so a reviewer's override changes the plan.

## 11. Security and governance

Runs offline with no credentials. Reads repositories through `git ls-files` and never executes their code; evidence holds paths and short match details, never file contents or secrets.

## 12. Observability

The report's gap table lists every capability below target with its first action.

## 13. Failure modes

| Failure | Behaviour |
|---|---|
| Target below current level | gap 0, no steps |
| Malformed capability or dimension id in targets | schema rejects it |

## 14. Mapping to Azure services

* **Azure DevOps Boards** or **GitHub Issues** can receive one work item per step (not automated here, by design).
* **Microsoft Foundry**: a hosted model replaces `MockLLM` for rationales, and Foundry evaluations score rationale groundedness against the cited evidence.
* **Microsoft Purview**: register the evidence store and reports as data assets with lineage back to the scanned repositories, and keep questionnaire answers under a sensitivity label.
* **Azure Policy**: audit that the evidence store stays keyless and versioned and that the Key Vault keeps RBAC, so the controls the assessment relies on cannot drift silently.
* **Azure Monitor / Log Analytics**: job logs, blob access logs and Key Vault audit events land in one workspace, where a query can trend maturity runs over time.

## 15. Limitations

* Actions are generic per level; tailoring them is the reviewer's job.

## 16. Interview talking points

* "Every gap names the missing evidence, so 'done' means the next scan can see it."

## 17. Adopt this

1. Set `targets` in `org.yaml`.
2. Rewrite actions for your context in `framework/framework.yaml` (keep the CC BY-SA notice).
3. Export gaps with `aimaturity assess --json` or the MCP `gaps` tool.
