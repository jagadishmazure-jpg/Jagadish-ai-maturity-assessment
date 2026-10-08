"""Infrastructure and workflow structure, checked offline (no Terraform or Bicep binaries needed)."""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"
TF = ROOT / "infra/terraform"
BICEP = ROOT / "infra/bicep"


def tf_text():
    return (TF / "main.tf").read_text()


def bicep_text():
    return "\n".join(p.read_text() for p in BICEP.rglob("*.bicep"))


@pytest.mark.parametrize(
    ("tf", "bicep"),
    [
        ("azurerm_log_analytics_workspace", "Microsoft.OperationalInsights/workspaces"),
        ("azurerm_storage_account", "Microsoft.Storage/storageAccounts"),
        ("azurerm_key_vault", "Microsoft.KeyVault/vaults"),
        ("azurerm_container_app_environment", "Microsoft.App/managedEnvironments"),
        ("azurerm_container_app_job", "Microsoft.App/jobs"),
        ("azurerm_user_assigned_identity", "Microsoft.ManagedIdentity/userAssignedIdentities"),
        ("azurerm_role_assignment", "Microsoft.Authorization/roleAssignments"),
        ("azurerm_monitor_diagnostic_setting", "Microsoft.Insights/diagnosticSettings"),
    ],
)
def test_both_stacks_declare_the_same_resources(tf, bicep):
    assert f'resource "{tf}"' in tf_text()
    assert bicep in bicep_text()


def test_smallest_skus_terraform():
    t = tf_text()
    assert '"PerGB2018"' in t and '"LRS"' in t and 'sku_name                   = "standard"' in t
    assert "cpu     = 0.25" in t and 'memory  = "0.5Gi"' in t


def test_smallest_skus_bicep():
    b = bicep_text()
    assert "'PerGB2018'" in b and "'Standard_LRS'" in b and "name: 'standard'" in b
    assert "cpu: json('0.25')" in b and "memory: '0.5Gi'" in b


def test_log_analytics_capped():
    v = (TF / "variables.tf").read_text()
    assert re.search(r'variable "log_daily_quota_gb"[\s\S]*?default\s*=\s*0.5', v)
    assert re.search(r'variable "log_retention_days"[\s\S]*?default\s*=\s*30', v)
    assert "dailyQuotaGb: json('0.5')" in bicep_text()


def test_evidence_store_keyless_and_versioned():
    assert "shared_access_key_enabled       = false" in tf_text() and "versioning_enabled = true" in tf_text()
    assert "allowSharedKeyAccess: false" in bicep_text() and "isVersioningEnabled: true" in bicep_text()


def test_three_private_containers_in_both_stacks():
    assert '["evidence", "reports", "audit"]' in (TF / "locals.tf").read_text()
    assert "['evidence', 'reports', 'audit']" in bicep_text()


def test_key_vault_rbac_and_purge_protection():
    t, b = tf_text(), bicep_text()
    assert "rbac_authorization_enabled = true" in t and "purge_protection_enabled   = true" in t
    assert "enableRbacAuthorization: true" in b and "enablePurgeProtection: true" in b


def test_job_is_schedule_triggered_with_user_identity():
    t, b = tf_text(), bicep_text()
    assert "schedule_trigger_config" in t and 'type         = "UserAssigned"' in t
    assert "triggerType: 'Schedule'" in b and "type: 'UserAssigned'" in b


def test_job_roles_are_least_privilege():
    t = tf_text()
    assert t.count('resource "azurerm_role_assignment"') == 2
    assert '"Storage Blob Data Contributor"' in t and '"Key Vault Secrets User"' in t
    assert "Owner" not in t and 'Contributor"' not in t.replace("Data Contributor", "")


def test_job_image_and_command_match_package():
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert 'aimaturity-scheduled = "aimaturity.scheduled:main"' in pyproject
    assert '["aimaturity-scheduled"]' in tf_text() and "['aimaturity-scheduled']" in bicep_text()
    assert 'ENTRYPOINT ["aimaturity-scheduled"]' in (ROOT / "Dockerfile").read_text()


def test_dockerfile_runs_as_non_root():
    d = (ROOT / "Dockerfile").read_text()
    assert "USER assessor" in d and "useradd" in d


def test_dev_weekly_prod_monthly():
    assert 'job_schedule = "0 6 * * 1"' in (TF / "envs/dev.tfvars").read_text()
    assert 'job_schedule = "0 5 1 * *"' in (TF / "envs/prod.tfvars").read_text()


def test_bicep_parameters_file():
    p = json.loads((BICEP / "main.parameters.json").read_text())["parameters"]
    assert p["environment"]["value"] == "dev" and p["jobEnabled"]["value"] is True


def test_checkov_skips_are_all_justified():
    lines = (ROOT / ".checkov.yaml").read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("- CKV"):
            j = i - 1
            while lines[j].strip().startswith("- CKV"):
                j -= 1
            assert lines[j].strip().startswith("#"), line


def test_terraform_tests_cover_dev_off_and_prod():
    t = (TF / "tests/plan.tftest.hcl").read_text()
    for run in ("dev_assessment_plane", "job_can_be_switched_off", "prod_monthly"):
        assert f'run "{run}"' in t
    assert 'mock_provider "azurerm"' in t


def wf(name):
    return yaml.safe_load((WF / name).read_text())


@pytest.mark.parametrize("name", ["ci.yml", "infra.yml", "deploy.yml", "teardown.yml"])
def test_workflow_parses_with_read_only_default(name):
    d = wf(name)
    assert d["permissions"] == {"contents": "read"}


def test_ci_runs_every_gate():
    text = (WF / "ci.yml").read_text()
    for cmd in (
        "pytest -q",
        "aimaturity evals",
        "aimaturity report --all --check",
        "render_docs.py --check",
        "aimaturity validate",
        "aimaturity links",
    ):
        assert cmd in text
    assert "\\.pdf$" in text


def test_deploy_is_gated_and_uses_oidc():
    d = wf("deploy.yml")
    jobs = d["jobs"]
    for name in ("image", "deploy-dev", "deploy-prod"):
        assert "vars.DEPLOY_ENABLED == 'true'" in jobs[name]["if"]
    for name in ("deploy-dev", "deploy-prod"):
        assert jobs[name]["permissions"]["id-token"] == "write"
        assert any("azure/login" in s.get("uses", "") for s in jobs[name]["steps"])
    assert jobs["deploy-dev"]["environment"] == "dev" and jobs["deploy-prod"]["environment"] == "prod"
    assert "deploy-dev" in jobs["deploy-prod"]["needs"]
    on = d[True] if True in d else d["on"]
    assert on["workflow_dispatch"]["inputs"]["deploy_tool"]["options"] == ["terraform", "bicep"]
    text = (WF / "deploy.yml").read_text()
    assert "client-secret" not in text and "AZURE_CLIENT_SECRET" not in text


def test_preflight_is_the_only_ungated_deploy_job():
    jobs = wf("deploy.yml")["jobs"]
    assert [n for n, j in jobs.items() if "DEPLOY_ENABLED" not in str(j.get("if", ""))] == ["preflight"]


def test_teardown_needs_gate_and_confirmation():
    job = wf("teardown.yml")["jobs"]["teardown"]
    assert "vars.DEPLOY_ENABLED == 'true'" in job["if"] and "inputs.confirm == inputs.environment" in job["if"]


def test_deploy_script_has_every_subcommand():
    text = (ROOT / ".github/scripts/deploy.sh").read_text()
    for fn in ("provision()", "smoke()", "run_job()", "destroy()"):
        assert fn in text
    assert "set -euo pipefail" in text


def test_workflows_are_hardened():
    """Supply-chain guard: every third-party action is pinned to a full commit SHA with a version
    comment, every workflow sets top-level permissions, CI runs gitleaks, and CodeQL and Dependabot
    are configured. Dependabot bumps keep the SHA and the comment together, so this stays green."""
    wf_dir = ROOT / ".github" / "workflows"
    for f in sorted(wf_dir.glob("*.yml")):
        text = f.read_text()
        assert re.search(r"^permissions:", text, re.M), f"{f.name}: no top-level permissions"
        for line in text.splitlines():
            m = re.search(r"\buses:\s*([^\s#]+)\s*(#.*)?$", line)
            if m and not m.group(1).startswith("./"):
                assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", m.group(1)), f"{f.name}: {line.strip()}"
                assert m.group(2) and re.match(r"#\s*v\d", m.group(2)), f"{f.name}: no version comment"
    assert "gitleaks/gitleaks-action@" in (wf_dir / "ci.yml").read_text()
    assert "github/codeql-action/analyze@" in (wf_dir / "codeql.yml").read_text()
    deps = (ROOT / ".github" / "dependabot.yml").read_text()
    assert "package-ecosystem: github-actions" in deps and "interval: weekly" in deps
