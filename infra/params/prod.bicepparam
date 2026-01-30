using '../main.bicep'

param location = 'germanywestcentral'

param functionAppName = 'paperpilot-api'

// Must be globally unique; adjust if the name is taken on first deploy.
param keyVaultName = 'paperpilot-kv-prod'

param tags = {
  app: 'PaperPilot'
  env: 'prod'
  managedBy: 'bicep'
}

