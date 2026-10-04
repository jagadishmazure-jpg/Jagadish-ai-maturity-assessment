// AI maturity assessment plane (Bicep twin of infra/terraform): a resource group with Log Analytics,
// the evidence store, a Key Vault and a scheduled Container Apps job with a user-assigned identity.
targetScope = 'subscription'

@allowed(['dev', 'prod'])
param environment string = 'dev'
@allowed(['eastus2', 'westus2', 'westeurope'])
param location string = 'eastus2'
@description('Log Analytics retention in days (30 is the free-retention minimum)')
param logRetentionDays int = 30
@description('Container image the scheduled assessment job runs')
param jobImage string = 'ghcr.io/jagadishmazure-jpg/ai-maturity-assessment:0.1.0'
@description('Cron expression (UTC) for the scheduled re-assessment')
param jobSchedule string = '0 6 * * 1'
@description('Create the Container Apps environment and job')
param jobEnabled bool = true

var region = { eastus2: 'eus2', westus2: 'wus2', westeurope: 'weu' }[location]
var suffix = '${environment}-${region}-001'
var tags = {
  env: environment
  owner: 'ai-governance-office'
  app: 'ai-maturity-assessment'
  'cost-center': 'CC-7200'
  'managed-by': 'bicep'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-aimaturity-${suffix}'
  location: location
  tags: tags
}

module evidence 'modules/evidence.bicep' = {
  name: 'aimaturity-evidence'
  scope: rg
  params: {
    location: location
    suffix: suffix
    storageName: take(replace('staimaturity${environment}${region}001', '-', ''), 24)
    tags: tags
    logRetentionDays: logRetentionDays
  }
}

module job 'modules/job.bicep' = if (jobEnabled) {
  name: 'aimaturity-job'
  scope: rg
  params: {
    location: location
    suffix: suffix
    tags: tags
    image: jobImage
    schedule: jobSchedule
    environmentName: environment
    workspaceName: evidence.outputs.workspaceName
    storageAccountName: evidence.outputs.storageAccount
    keyVaultName: evidence.outputs.keyVaultName
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output EVIDENCE_STORAGE_ACCOUNT string = evidence.outputs.storageAccount
output KEY_VAULT_URI string = evidence.outputs.keyVaultUri
output ASSESSMENT_JOB_NAME string = jobEnabled ? job!.outputs.jobName : ''
