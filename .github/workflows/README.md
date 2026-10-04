# workflows

Workflows. Deploy and teardown need `DEPLOY_ENABLED == 'true'`, which is not set. See docs/infra/workflows.md.

| File | What it does |
|---|---|
| `ci.yml` | Lint, validate, tests, eval gates, report and doc drift, PDF guard, Bicep build, image build |
| `infra.yml` | Terraform fmt/validate/test, tflint, checkov, plan when OIDC variables exist |
| `deploy.yml` | Image to GHCR, dev, prod with approval; Terraform or Bicep; OIDC |
| `teardown.yml` | Manual, gated, typed confirmation |
