# AI maturity assessment plane: a versioned, keyless evidence store, Log Analytics, a Key Vault
# for the optional LLM endpoint secret, and a Container Apps job that re-runs the assessments on
# a schedule with a user-assigned identity. Smallest SKUs; nothing here serves traffic.

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.short}-${local.suffix}"
  location = var.location
  tags     = local.tags
}

# --- Observability: one workspace for job logs, Key Vault audit events and blob access logs
resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${local.short}-${local.suffix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  daily_quota_gb      = var.log_daily_quota_gb
  tags                = local.tags
}

# --- Evidence store: snapshots, questionnaires, reports and HITL audit logs
resource "azurerm_storage_account" "evidence" {
  name                            = substr(replace("st${local.short}${var.environment}${local.region}001", "-", ""), 0, 24)
  resource_group_name             = azurerm_resource_group.this.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  tags                            = local.tags

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
  }
}

resource "azurerm_storage_container" "evidence" {
  for_each              = toset(local.evidence_containers)
  name                  = each.key
  storage_account_id    = azurerm_storage_account.evidence.id
  container_access_type = "private"
}

resource "azurerm_monitor_diagnostic_setting" "evidence_blob" {
  name                       = "diag-evidence-blob"
  target_resource_id         = "${azurerm_storage_account.evidence.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "StorageRead"
  }
  enabled_log {
    category = "StorageWrite"
  }
  enabled_log {
    category = "StorageDelete"
  }
}

# --- Key Vault (RBAC, standard): holds the optional hosted-LLM endpoint key; offline runs need none
resource "azurerm_key_vault" "this" {
  name                       = "kv-aimat-${local.suffix}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = var.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
  tags                       = local.tags
}

resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  name                       = "diag-kv-audit"
  target_resource_id         = azurerm_key_vault.this.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "AuditEvent"
  }
}

# --- Scheduled assessments: Container Apps environment (consumption) and a cron-triggered job
resource "azurerm_user_assigned_identity" "job" {
  name                = "id-${local.short}-job-${local.suffix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  tags                = local.tags
}

resource "azurerm_role_assignment" "job_blob" {
  scope                = azurerm_storage_account.evidence.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.job.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "job_secrets" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.job.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_container_app_environment" "this" {
  count                      = var.job_enabled ? 1 : 0
  name                       = "cae-${local.short}-${local.suffix}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  tags                       = local.tags
}

resource "azurerm_container_app_job" "assess" {
  count                        = var.job_enabled ? 1 : 0
  name                         = "caj-${local.short}-${local.suffix}"
  resource_group_name          = azurerm_resource_group.this.name
  location                     = var.location
  container_app_environment_id = azurerm_container_app_environment.this[0].id
  replica_timeout_in_seconds   = 1800
  replica_retry_limit          = 1
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.job.id]
  }

  schedule_trigger_config {
    cron_expression          = var.job_schedule
    parallelism              = 1
    replica_completion_count = 1
  }

  template {
    container {
      name    = "assess"
      image   = var.job_image
      cpu     = 0.25
      memory  = "0.5Gi"
      command = ["aimaturity-scheduled"]

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.job.client_id
      }
      env {
        name  = "EVIDENCE_STORAGE_ACCOUNT"
        value = azurerm_storage_account.evidence.name
      }
      env {
        name  = "KEY_VAULT_URI"
        value = azurerm_key_vault.this.vault_uri
      }
      env {
        name  = "AIMATURITY_ENV"
        value = var.environment
      }
    }
  }

  depends_on = [azurerm_role_assignment.job_blob, azurerm_role_assignment.job_secrets]
}
