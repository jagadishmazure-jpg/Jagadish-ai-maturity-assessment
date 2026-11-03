# Changelog

## Unreleased

### Added

- Threat model (`docs/security/threat-model.md`): STRIDE, OWASP Top 10 for LLM Applications and MITRE ATLAS mapped to this repository's components, each row with its control, test evidence and built / planned status.
- SBOM job in CI: an SPDX JSON software bill of materials of the source tree on every run (artifact `sbom.spdx.json`).
- Container supply chain: base images pinned by digest, pip/uv removed from runtime images, a Trivy image scan that fails on fixable HIGH/CRITICAL findings, an image SBOM, and keyless build provenance for the image archive on `main` (`actions/attest-build-provenance`; verification steps in `SECURITY.md`).
- Supply-chain hardening: every GitHub Action pinned to a commit SHA with a version comment, top-level `permissions` on every workflow, a gitleaks job in CI, a CodeQL workflow, `.github/dependabot.yml` and a guard test (`test_workflows_are_hardened`).
- GitHub settings: Dependabot alerts and security updates, private vulnerability reporting and a `main` ruleset (no force-push or deletion; CI required on pull requests).
- Portfolio sample: the profile repository (written AI principles, roadmap, skills matrix) joins the
  scan, the evidence snapshot is refreshed from live checkouts, and reports and docs are re-rendered.
  Questionnaire answers stay labelled sample answers.
- Enterprise Agentic AI Maturity Model (EAMM): eight weighted dimensions, 23 capabilities and five
  levels (Explore, Prove, Operate, Scale, Optimise), each capability crosswalked to NIST AI RMF,
  ISO/IEC 42001 and the EU AI Act. Design rationale in ADR 0007.
- Rubric of 76 evidence signals with must and support criteria per level, an evidence ceiling from
  Scale upwards, default anchors per dimension and a 48-item questionnaire.
- Collectors for repositories and evidence snapshots; stepwise scoring with confidence and citations.
- Dimension and weighted overall rollup with anchor caps and a 0-100 Agentic Readiness Index.
- Standards crosswalk doc (`docs/standards-crosswalk.md`) generated from the model and kept in step by a test; one doc per dimension.
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
