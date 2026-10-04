# tests

pytest suite (offline). `pytest -q`.

| File | What it does |
|---|---|
| `conftest.py` | Shared assessments and a writable org copy |
| `test_framework.py` | Framework model and rubric shape |
| `test_signals.py` | Every signal matches its example |
| `test_questionnaire.py` | Answers and labels |
| `test_scoring.py` | Levels and confidence |
| `test_rollup.py` | Medians and caps |
| `test_hitl.py` | Reviews and audit chain |
| `test_gaps_roadmap.py` | Gaps and scheduling |
| `test_agent.py` | Graph and verifier |
| `test_orgs_sources.py` | Sources, snapshot, manifests |
| `test_samples.py` | Sample results, labels, cross-links |
| `test_report.py` | Report drift and content |
| `test_evals.py` | Eval gates |
| `test_mcp_a2a.py` | MCP tools and agent card |
| `test_cli.py` | CLI commands and scheduled run |
| `test_iac.py` | Terraform, Bicep, workflows |
| `test_repo_hygiene.py` | Docs, dates, attribution, PDF guard, overlap, READMEs |
