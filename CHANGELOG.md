# Changelog

## Unreleased

- Portfolio sample: the profile repository (written AI principles, roadmap, skills matrix) joins the
  scan, the evidence snapshot is refreshed from live checkouts, and reports and docs are re-rendered.
  Questionnaire answers stay labelled sample answers.
- Machine-readable framework model: 6 pillars, 29 categories and 5 levels with descriptors in
  original wording (CC BY-SA 3.0 IGO in `framework/`).
- Rubric of 76 evidence signals, per-level mapping and a 44-item questionnaire.
- Collectors for repositories and evidence snapshots; stepwise scoring with confidence and citations.
- Pillar and overall rollup with critical-category caps.
- HITL review queue with digest-bound sign-off and a hash-chained audit log.
- Gap analysis, Month 1-12 roadmap with quick wins, strategic items and dependencies.
- Executive report in Markdown and HTML with a radar chart.
- Assessor agent graph with a mock LLM and citation verifier.
- Eval gates: scoring stability, citation completeness, calibration against labelled samples.
- MCP server with 9 read-only tools and an A2A agent card.
- Sample assessments: my portfolio, Kestrel Bay Bank and Valemont Revenue Agency.
- Terraform and Bicep for the evidence store, Log Analytics, Key Vault and a scheduled
  Container Apps job; CI, infra, gated deploy and teardown workflows.
- Full documentation set with rendered outputs, ADRs, implementation, interview and adopt guides.
