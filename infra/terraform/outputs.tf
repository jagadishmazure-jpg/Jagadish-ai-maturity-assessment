output "AZURE_RESOURCE_GROUP" {
  value = azurerm_resource_group.this.name
}

output "EVIDENCE_STORAGE_ACCOUNT" {
  value = azurerm_storage_account.evidence.name
}

output "KEY_VAULT_URI" {
  value = azurerm_key_vault.this.vault_uri
}

output "LOG_ANALYTICS_WORKSPACE_ID" {
  value = azurerm_log_analytics_workspace.this.id
}

output "ASSESSMENT_JOB_NAME" {
  value = var.job_enabled ? azurerm_container_app_job.assess[0].name : ""
}
