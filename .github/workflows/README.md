# workflows

Workflows. Deploy and teardown need `DEPLOY_ENABLED == 'true'`, which is not set. See docs/infra/workflows.md.

| File | What it does |
|---|---|
| `ci.yml` | Lint, validate, tests, eval gates, report and doc drift, PDF guard, Bicep build, image build; a `secrets` job runs gitleaks over the full git history. |
| `codeql.yml` | CodeQL for Python and for the workflow files (`actions`), on push, pull request and weekly. Results appear under Security -> Code scanning and do not fail the build. |
| `infra.yml` | Terraform fmt/validate/test, tflint, checkov, plan when OIDC variables exist |
| `deploy.yml` | Image to GHCR, dev, prod with approval; Terraform or Bicep; OIDC |
| `teardown.yml` | Manual, gated, typed confirmation |

**Supply chain.** Every third-party action is pinned to a full commit SHA with the version in a comment, and every workflow starts from `permissions: contents: read`; jobs that need more (OIDC sign-in, CodeQL uploads) ask for it themselves. Dependabot ([`../dependabot.yml`](../dependabot.yml)) proposes weekly grouped updates that move the SHA and the comment together, and `tests/test_iac.py::test_workflows_are_hardened` fails CI if an action is left unpinned.
