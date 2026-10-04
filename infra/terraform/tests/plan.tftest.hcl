# Offline plan tests: mocked provider, no Azure credentials, nothing created.
#   terraform init -backend=false && terraform test
mock_provider "azurerm" {
  mock_data "azurerm_client_config" {
    defaults = {
      tenant_id       = "00000000-0000-0000-0000-000000000001"
      subscription_id = "00000000-0000-0000-0000-000000000002"
      object_id       = "00000000-0000-0000-0000-000000000003"
    }
  }
  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id"
      principal_id = "00000000-0000-0000-0000-000000000004"
      client_id    = "00000000-0000-0000-0000-000000000005"
    }
  }
  mock_resource "azurerm_storage_account" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/st"
    }
  }
  mock_resource "azurerm_key_vault" {
    defaults = {
      id        = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg/providers/Microsoft.KeyVault/vaults/kv"
      vault_uri = "https://kv.vault.azure.net/"
    }
  }
  mock_resource "azurerm_log_analytics_workspace" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/log"
    }
  }
  mock_resource "azurerm_container_app_environment" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg/providers/Microsoft.App/managedEnvironments/cae"
    }
  }
}

run "dev_assessment_plane" {
  command = plan

  variables {
    environment = "dev"
  }

  assert {
    condition     = azurerm_resource_group.this.name == "rg-aimaturity-dev-eus2-001"
    error_message = "resource group must follow the CAF naming pattern"
  }

  assert {
    condition     = azurerm_log_analytics_workspace.this.sku == "PerGB2018" && azurerm_log_analytics_workspace.this.retention_in_days == 30 && azurerm_log_analytics_workspace.this.daily_quota_gb == 0.5
    error_message = "smallest Log Analytics settings with a daily cap"
  }

  assert {
    condition     = azurerm_storage_account.evidence.account_replication_type == "LRS" && azurerm_storage_account.evidence.blob_properties[0].versioning_enabled && !azurerm_storage_account.evidence.shared_access_key_enabled
    error_message = "evidence store: smallest replication, versioned, keyless"
  }

  assert {
    condition     = length(azurerm_storage_container.evidence) == 3 && alltrue([for c in azurerm_storage_container.evidence : c.container_access_type == "private"])
    error_message = "three private containers: evidence, reports, audit"
  }

  assert {
    condition     = azurerm_key_vault.this.sku_name == "standard" && azurerm_key_vault.this.rbac_authorization_enabled && azurerm_key_vault.this.purge_protection_enabled
    error_message = "Key Vault: standard SKU, RBAC, purge protection"
  }

  assert {
    condition     = length(azurerm_key_vault.this.name) <= 24
    error_message = "Key Vault names are limited to 24 characters"
  }

  assert {
    condition     = azurerm_container_app_job.assess[0].schedule_trigger_config[0].cron_expression == "0 6 * * 1"
    error_message = "the job re-runs assessments weekly in dev"
  }

  assert {
    condition     = azurerm_container_app_job.assess[0].template[0].container[0].cpu == 0.25 && azurerm_container_app_job.assess[0].template[0].container[0].memory == "0.5Gi"
    error_message = "smallest Container Apps job size"
  }

  assert {
    condition     = azurerm_container_app_job.assess[0].identity[0].type == "UserAssigned"
    error_message = "the job authenticates with its user-assigned identity, never a key"
  }

  assert {
    condition     = azurerm_role_assignment.job_blob.role_definition_name == "Storage Blob Data Contributor" && azurerm_role_assignment.job_secrets.role_definition_name == "Key Vault Secrets User"
    error_message = "least-privilege data-plane roles for the job"
  }
}

run "job_can_be_switched_off" {
  command = plan

  variables {
    environment = "dev"
    job_enabled = false
  }

  assert {
    condition     = length(azurerm_container_app_job.assess) == 0 && length(azurerm_container_app_environment.this) == 0
    error_message = "no Container Apps resources when the job is disabled"
  }
}

run "prod_monthly" {
  command = plan

  variables {
    environment  = "prod"
    job_schedule = "0 5 1 * *"
  }

  assert {
    condition     = azurerm_resource_group.this.name == "rg-aimaturity-prod-eus2-001" && azurerm_container_app_job.assess[0].schedule_trigger_config[0].cron_expression == "0 5 1 * *"
    error_message = "prod re-assesses monthly"
  }
}
