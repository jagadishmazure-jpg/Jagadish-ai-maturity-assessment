# terraform

Terraform (azurerm ~> 4.50). `terraform init -backend=false && terraform test`.

| File | What it does |
|---|---|
| `main.tf` | Resources |
| `variables.tf` | Inputs |
| `locals.tf` | Names and tags |
| `outputs.tf` | Outputs |
| `providers.tf` | Provider features |
| `versions.tf` | Version pins |
| `backend.tf` | Remote state (Entra ID) |
| `.tflint.hcl` | tflint rules |
| `envs/` | Per-environment values |
| `tests/` | Offline plan tests |
