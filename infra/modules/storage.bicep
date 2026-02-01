@description('Storage account name.')
param accountName string

@description('Storage account location (must match existing region).')
param location string

@description('Optional tag set applied to newly created resources.')
param tags object = {}

@description('Blob container names to ensure exist.')
param blobContainerNames array = []

@description('Azure Files share name used by the Function App content mount (if any).')
param fileShareName string = ''

@description('Azure Files share quota in MB.')
param fileShareQuotaMb int = 102400

resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: accountName
  location: location
  kind: 'Storage'
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    allowSharedKeyAccess: true
    defaultToOAuthAuthentication: true
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
    }
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = {
  parent: storage
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: false
    }
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2025-01-01' = {
  parent: storage
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
    protocolSettings: {
      smb: {}
    }
    shareDeleteRetentionPolicy: {
      days: 7
      enabled: true
    }
  }
}

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = [for containerName in blobContainerNames: {
  parent: blobService
  name: containerName
  properties: {
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }
}]

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2025-01-01' = if (fileShareName != '') {
  parent: fileService
  name: fileShareName
  properties: {
    shareQuota: fileShareQuotaMb
  }
}

output storageAccountId string = storage.id

