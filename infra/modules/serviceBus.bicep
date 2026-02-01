@description('Service Bus namespace name.')
param namespaceName string

@description('Service Bus location (must match existing region).')
param location string

@description('Service Bus SKU name (e.g. Basic, Standard, Premium).')
param skuName string = 'Basic'

@description('Service Bus queue name.')
param queueName string

@description('Optional tag set applied to newly created resources.')
param tags object = {}

resource sbNamespace 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: namespaceName
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  properties: {
    disableLocalAuth: false
    minimumTlsVersion: '1.2'
    premiumMessagingPartitions: 0
    publicNetworkAccess: 'Enabled'
    zoneRedundant: true
  }
}

resource networkRuleSet 'Microsoft.ServiceBus/namespaces/networkrulesets@2024-01-01' = {
  parent: sbNamespace
  name: 'default'
  properties: {
    defaultAction: 'Allow'
    ipRules: []
    publicNetworkAccess: 'Enabled'
    trustedServiceAccessEnabled: false
    virtualNetworkRules: []
  }
}

resource queue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  parent: sbNamespace
  name: queueName
  properties: {
    autoDeleteOnIdle: 'P10675199DT2H48M5.4775807S'
    deadLetteringOnMessageExpiration: false
    defaultMessageTimeToLive: 'P14D'
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    enableBatchedOperations: true
    enableExpress: false
    enablePartitioning: false
    lockDuration: 'PT5M'
    maxDeliveryCount: 10
    maxMessageSizeInKilobytes: 256
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: false
    requiresSession: false
    status: 'Active'
  }
}

output serviceBusNamespaceId string = sbNamespace.id
output serviceBusQueueId string = queue.id

