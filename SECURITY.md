# Security policy

## Scope

This repository holds offline code, synthetic sample data for fictional organisations, a frozen
evidence snapshot of my own public repositories, and infrastructure templates. It contains no
credentials, subscription or tenant identifiers, model keys, or personal data, and its tests check
for that.

## Reporting a vulnerability

Please open a private security advisory on GitHub (Security tab, "Report a vulnerability") instead
of a public issue. Include the file, the problem and steps to reproduce.

## Design choices that matter for security

- **Read-only collection.** Collectors only read files under the configured roots, refuse paths
  that escape them, skip binaries and large files, and never execute anything they find.
- **No secrets.** GitHub Actions authenticate to Azure with OIDC federated credentials; storage has
  shared keys disabled; the scheduled job uses a managed identity; Key Vault uses RBAC.
- **Tamper-evident sign-off.** Reviews are bound to a digest of the evidence, a reviewer cannot sign
  their own assessment, and the audit log is hash-chained and verified in CI.
- **Grounded rationales.** The citation verifier rejects any rationale that cites evidence the
  collectors did not produce.
- **Read-only MCP server.** Every tool is annotated read-only and non-destructive.
- **Gated deploy.** Deploy and teardown do nothing until `DEPLOY_ENABLED` is set; prod needs
  environment reviewers.
- **Scanned IaC.** checkov and tflint run on Terraform; each skipped check is justified in
  `.checkov.yaml`.

## Supported versions

Only the `main` branch is maintained.
