@description('Location for the Key Vault.')
param location string

@description('Name for the Key Vault.')
param keyVaultName string

@description('Optional tag set applied to the Key Vault.')
param tags object = {}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    // Use RBAC for access management (preferred for automation).
    enableRbacAuthorization: true
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    publicNetworkAccess: 'Enabled'
    softDeleteRetentionInDays: 90
  }
}

output vaultUri string = kv.properties.vaultUri
output keyVaultResourceId string = kv.id

