# Best practices

The rules this repository follows, and what enforces each one.

| Practice | Enforced by |
|---|---|
| Every number in a doc comes from a fresh run | `render_docs.py --check` in CI |
| Checked-in reports match the code | `aimaturity report --all --check` in CI |
| Every category result cites evidence | `citations` eval gate |
| The assessor is deterministic | `stability` eval gate (shuffle, dropout locality) |
| Scores agree with expert labels | `calibration` eval gate |
| Demo inputs never pass as facts | `sample-answers` label, forced review, report banner, tests |
| The agent never approves itself | `validate_review`, tests |
| Approvals expire with their evidence | digest binding, stale status, tests |
| Audit trail is tamper-evident | hash chain, `verify_audit_log`, tests |
| Read-only scanning | `git ls-files` only, mtime test |
| Source PDF never committed | `.gitignore` `*.pdf`, hygiene test, CI step |
| Framework text in own words | 8-word overlap check against the source text = 0 |
| Attribution with license name and link | README, `framework/LICENSE.md`, reports, pillar docs, hygiene test |
| No dates in docs | hygiene test (ISO dates, years, month names) |
| Fictional organisations only | hygiene test bans real names and personal addresses |
| A README with a file table in every folder | hygiene test |
| Every full doc has 17 sections, mermaid, output and code | hygiene test |
| Smallest SKUs and no keys | `tests/test_iac.py`, `terraform test`, checkov with justified skips |
| Deploy off by default, OIDC only, prod approval | `tests/test_iac.py` on the workflows |
| Small, reviewable commits | git history |
