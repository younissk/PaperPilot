@description('Existing Function App name to configure.')
param functionAppName string

@description('Key Vault name (used to build Key Vault references).')
param keyVaultName string

// Existing Function App (do not manage its full properties in Phase 1)
resource functionApp 'Microsoft.Web/sites@2022-03-01' existing = {
  name: functionAppName
}

// Read the current app settings so we can merge and avoid deleting platform settings.
var currentAppSettings = list('${functionApp.id}/config/appsettings', '2022-03-01').properties

// Key Vault reference helper (the secret must exist in KV; we do not store secret values in git).
var kvSecretUriPrefix = 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets'

// Secrets we will store in Key Vault (Phase 1). Values become references here.
// NOTE: This assumes you will create these secrets (one-time) after the vault exists.
var desiredAppSettings = {
  // Sensitive values: move to Key Vault
  OPENAI_API_KEY: '@Microsoft.KeyVault(SecretUri=${kvSecretUriPrefix}/OPENAI-API-KEY)'
  AZURE_COSMOS_KEY: '@Microsoft.KeyVault(SecretUri=${kvSecretUriPrefix}/AZURE-COSMOS-KEY)'
  AZURE_SERVICE_BUS_CONNECTION_STRING: '@Microsoft.KeyVault(SecretUri=${kvSecretUriPrefix}/AZURE-SERVICE-BUS-CONNECTION-STRING)'
}

resource appSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'appsettings'
  parent: functionApp
  properties: union(currentAppSettings, desiredAppSettings)
}

output appSettingsUpdated bool = true

