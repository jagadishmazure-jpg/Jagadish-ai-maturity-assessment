# Security policy

## Scope

This repository holds offline code, synthetic sample data for fictional organisations, a frozen
evidence snapshot of my own public repositories, and infrastructure templates. It contains no
credentials, subscription or tenant identifiers, model keys, or personal data, and its tests check
for that.

## Reporting a vulnerability

Please do not open a public issue with the details.

1. Open a private security advisory on GitHub (Security tab, "Report a vulnerability"). Include the
   file, the problem and steps to reproduce.
2. If that button is not shown, open an issue titled `Security contact request` with no technical
   details, and I will reply with a private channel.

I aim to acknowledge a report within 5 working days. This is a personal portfolio maintained by one
person, so there is no formal SLA or bug bounty.

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
- **Supply chain:** every third-party GitHub Action is pinned to a full commit SHA with its version in a comment, and every workflow starts from read-only `permissions`. Dependabot proposes weekly, grouped updates ([`.github/dependabot.yml`](.github/dependabot.yml)); CodeQL scans the Python code and the workflow files ([`codeql.yml`](.github/workflows/codeql.yml)); gitleaks scans the full git history in CI. A test (`test_workflows_are_hardened`) fails if an action is left unpinned or a workflow loses its `permissions` block.
- **Known scanner false positives** are listed by fingerprint in [`.gitleaksignore`](.gitleaksignore), each with the reason (for example a public Azure built-in role ID); none is a credential.
- **GitHub settings:** secret scanning with push protection, Dependabot alerts and security updates, private vulnerability reporting, and a ruleset on `main` that blocks force-pushes and branch deletion and requires the CI checks before a pull request can merge. The maintainer (repository admin) can still push directly to `main`, so for direct pushes the checks run after the push rather than before it.

## Supported versions

Only the `main` branch is maintained.
