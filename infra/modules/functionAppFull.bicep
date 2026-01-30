@description('Function App name.')
param functionAppName string

@description('Function App location (must match existing region).')
param location string

@description('App Service plan (serverfarm) name.')
param appServicePlanName string

@description('User-assigned managed identity name for the Function App.')
param userAssignedIdentityName string

@description('Linux runtime stack, e.g. Python|3.12.')
param linuxFxVersion string = 'Python|3.12'

@description('Allowed CORS origins for the Function App.')
param corsAllowedOrigins array = [
  'https://portal.azure.com'
]

@description('Optional custom domain to bind (e.g. api.example.com). Leave empty to skip.')
param customDomainName string = ''

@description('Optional Application Insights resource id (used to preserve the hidden-link tag).')
param appInsightsResourceId string = ''

@description('Optional tag set applied to newly created resources.')
param tags object = {}

var functionTags = appInsightsResourceId != '' ? union(tags, {
  'hidden-link: /app-insights-resource-id': appInsightsResourceId
}) : tags

// -----------------------------------------------------------------------------
// Dependencies (managed in IaC for repeatability)
// -----------------------------------------------------------------------------

resource uai 'Microsoft.ManagedIdentity/userAssignedIdentities@2025-01-31-preview' = {
  name: userAssignedIdentityName
  location: location
  tags: tags
}

resource plan 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: appServicePlanName
  location: location
  kind: 'functionapp'
  tags: tags
  sku: {
    capacity: 0
    family: 'Y'
    name: 'Y1'
    size: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    asyncScalingEnabled: false
    elasticScaleEnabled: false
    hyperV: false
    isSpot: false
    isXenon: false
    maximumElasticWorkerCount: 0
    perSiteScaling: false
    reserved: true
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

// -----------------------------------------------------------------------------
// Function App
// -----------------------------------------------------------------------------

resource functionApp 'Microsoft.Web/sites@2024-11-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: functionTags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uai.id}': {}
    }
  }
  properties: {
    clientAffinityEnabled: false
    enabled: true
    httpsOnly: true
    keyVaultReferenceIdentity: uai.id
    publicNetworkAccess: 'Enabled'
    reserved: true
    serverFarmId: plan.id
    siteConfig: {
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      functionAppScaleLimit: 200
      http20Enabled: false
      linuxFxVersion: linuxFxVersion
      minimumElasticInstanceCount: 1
      numberOfWorkers: 1
    }
    storageAccountRequired: false
  }
}

// -----------------------------------------------------------------------------
// Web config (CORS, FTPS, etc.)
// -----------------------------------------------------------------------------

resource webConfig 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: functionApp
  name: 'web'
  properties: {
    alwaysOn: false
    cors: {
      allowedOrigins: corsAllowedOrigins
      supportCredentials: false
    }
    ftpsState: 'FtpsOnly'
    linuxFxVersion: linuxFxVersion
    minTlsVersion: '1.2'
    scmType: 'GitHubAction'
  }
}

resource ftpPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: functionApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource scmPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: functionApp
  name: 'scm'
  properties: {
    allow: false
  }
}

resource customDomainBinding 'Microsoft.Web/sites/hostNameBindings@2024-11-01' = if (customDomainName != '') {
  parent: functionApp
  name: customDomainName
  properties: {
    hostNameType: 'Verified'
    siteName: functionAppName
  }
}

output functionAppId string = functionApp.id
output userAssignedIdentityId string = uai.id
output userAssignedPrincipalId string = uai.properties.principalId

