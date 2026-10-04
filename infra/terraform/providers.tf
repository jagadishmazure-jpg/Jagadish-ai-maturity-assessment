provider "azurerm" {
  features {
    key_vault {
      # A torn-down dev vault sits soft-deleted for 7 days; redeploying recovers it instead of failing.
      recover_soft_deleted_key_vaults = true
      purge_soft_delete_on_destroy    = false
    }
  }
  storage_use_azuread = true
}
