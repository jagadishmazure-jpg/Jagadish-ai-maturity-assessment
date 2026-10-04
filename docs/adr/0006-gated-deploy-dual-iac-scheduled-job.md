# ADR 0006: Dual IaC, a scheduled Container Apps job, deploy gated off

**Status:** Accepted

## Context

Teams standardise on Terraform or Bicep. Assessments should re-run on a schedule. This repository must
not create cloud resources by accident.

## Decision

Terraform and Bicep describe the same plane at the smallest SKUs (LRS storage, capped Log Analytics,
standard RBAC Key Vault, consumption Container Apps job). Tests enforce parity. Deploy uses OIDC, goes
dev then prod with approval, and every job except preflight requires `DEPLOY_ENABLED == 'true'`, which
is not set.

## Consequences

* Either tool works; drift between them fails tests.
* Nothing is deployed; turning it on is a documented, deliberate step.
