targetScope = 'resourceGroup'

@description('Location for new resources created by this template.')
param location string = resourceGroup().location

@description('Existing Function App name to configure.')
param functionAppName string

@description('Name of the Key Vault to create.')
param keyVaultName string

@description('Optional tag set applied to newly created resources.')
param tags object = {}

// Create Key Vault (Phase 1)
module keyVault 'modules/keyVault.bicep' = {
  name: 'keyVault'
  params: {
    location: location
    keyVaultName: keyVaultName
    tags: tags
  }
}

output keyVaultUri string = keyVault.outputs.vaultUri
output functionAppNameOut string = functionAppName

