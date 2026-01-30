using '../main.bicep'

param location = 'germanywestcentral'

param functionAppName = 'paperpilot-api'

param appServicePlanName = 'ASP-PaperPilot-87b9'

param userAssignedIdentityName = 'paperpilot-api-id-97d1'

// Must be globally unique; adjust if the name is taken on first deploy.
param keyVaultName = 'paperpilot-kv-prod'

param cosmosAccountName = 'paperpilot-jobs-db'

// Cosmos lives in a different region than the Function App.
param cosmosLocation = 'Switzerland North'

param cosmosSqlDatabaseName = 'Jobs'

param cosmosContainerName = 'jobs'

// Exported from the live resource group.
param cosmosIpRules = [
  {
    ipAddressOrRange: '0.0.0.0'
  }
  {
    ipAddressOrRange: '193.83.29.132'
  }
  {
    ipAddressOrRange: '4.210.172.107'
  }
  {
    ipAddressOrRange: '13.88.56.148'
  }
  {
    ipAddressOrRange: '13.91.105.215'
  }
  {
    ipAddressOrRange: '40.91.218.243'
  }
]

param serviceBusNamespaceName = 'paperpilot-prod'

param serviceBusQueueName = 'paperpilot-jobs'

param storageAccountName = 'paperpilot91b3'

param storageBlobContainerNames = [
  'azure-webjobs-hosts'
  'azure-webjobs-secrets'
  'github-actions-deploy'
  'results'
  'scm-releases'
]

param storageFileShareName = 'paperpilot-apiac1b'

param functionCorsAllowedOrigins = [
  'https://portal.azure.com'
  'https://papernavigator.com'
  'http://localhost:4321'
]

param functionCustomDomainName = 'api.papernavigator.com'

param appInsightsResourceId = '/subscriptions/063b2765-3fb9-436d-ade8-1c0d89f9bfeb/resourceGroups/PaperPilot/providers/Microsoft.Insights/components/paperpilot-api'

param tags = {
  app: 'PaperPilot'
  env: 'prod'
  managedBy: 'bicep'
}

