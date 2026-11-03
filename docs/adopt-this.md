# Adopt this

How another team reuses, configures and extends the assessor. Every component and dimension doc ends with its
own "Adopt this" section; this page is the overview.

## Reuse as is

1. Fork, `pip install -e ".[dev]"`, add `samples/<your-org>/` (copy `portfolio/` for real repositories or `kestrel-bay-bank/` for a manifest).
2. Collect, answer the questionnaire, assess, review, report:

```bash
aimaturity collect --org <org> --live --write
aimaturity assess --org <org>
aimaturity review --org <org> --capability <id> --reviewer "<name>" --decision confirm --comment "<evidence>"
aimaturity report --org <org>
```

## Configure

| What | Where |
|---|---|
| Targets (default, per dimension, per capability) | `samples/<org>/org.yaml` `targets` |
| Anchor capabilities | `org.yaml` `anchors` (defaults in `rubric/capabilities.yaml`) |
| Dimension weights | `framework/framework.yaml` (change with an ADR) |
| Roadmap capacity | `org.yaml` `capacity` |
| Must and support criteria for each level | `rubric/capabilities.yaml` |
| What a signal looks for | `rubric/signals.yaml` |
| Questions | `rubric/questionnaire.yaml` |
| Support share and review bar | `rubric/capabilities.yaml` `support_share`, `scoring.REVIEW_BELOW` |
| Eval thresholds | `evals/thresholds.yaml` |
| Schedule and image | `infra/terraform/envs/*.tfvars` or Bicep parameters |

## Extend

* **New signal**: add it with an example; the tests require the example to match, and `aimaturity validate` requires it to be used by a capability.
* **New source** (wiki export, API): implement `files()` and `read()` like `ManifestSource`.
* **Hosted LLM**: pass an object with `rationale(facts)` as `llm=`; the verifier stays.
* **New report section**: add it in `report.build_content`; Markdown and HTML both pick it up.
* **New MCP tool**: add it in `mcp_server.build_server` with the read-only annotation and a test.
* **New eval gate**: return `{gate, ok, ...}` from a function and append it in `evals.run_all`.

## Change the model deliberately

New dimensions, levels, weights or evidence rules are design changes: record them in an ADR next to
ADR 0007, run `aimaturity validate` and `aimaturity evals`, and re-render reports and docs. The
repository is MIT licensed throughout.
