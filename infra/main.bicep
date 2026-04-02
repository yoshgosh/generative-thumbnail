@description('Organization name')
param organizationName string = 'yosh'

@description('Project name')
param projectName string = 'gtn'

@description('Deployment environment (dev, prd)')
@allowed(['dev', 'prd'])
param env string

@description('Resource deployment location')
param location string = 'japaneast'
var locationCode = 'jpe'

var uniqueId = uniqueString(resourceGroup().id)
var shortUniqueId = take(uniqueId, 5)

// ----- naming -----
// logging
var lawName = 'law-${organizationName}-${projectName}-${env}-${locationCode}'

// storage
var imgsStName = take('st${organizationName}${projectName}imgs${env}${locationCode}${shortUniqueId}', 24)
var imgsContainerName = 'images'


// generate-api
var generateApiAppiName = 'appi-${organizationName}-${projectName}-generate-api-${env}-${locationCode}'
var generateApiStName = take('st${organizationName}${projectName}gapi${env}${locationCode}${shortUniqueId}', 24)
var generateApiContainerName = 'api-package'
var generateApiAspName = 'asp-${organizationName}-${projectName}-generate-api-${env}-${locationCode}'
var generateApiFuncName = 'func-${organizationName}-${projectName}-generate-api-${env}-${locationCode}'

// display-web
var displayWebName = 'stapp-${organizationName}-${projectName}-display-web-${env}-${locationCode}'

// ----- resources -----
// logging
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: lawName
  location: location
  properties: { sku: { name: 'PerGB2018' } }
}

// storage
resource imgsSt 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: imgsStName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  resource blobServices 'blobServices' existing = {
    name: 'default'
  }
}

resource imgsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: imgsSt::blobServices
  name: imgsContainerName
}

// generate-api
resource generateApiAppi 'Microsoft.insights/components@2020-02-02' = {
  name: generateApiAppiName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource generateApiSt 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: generateApiStName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  resource blobServices 'blobServices' existing = {
    name: 'default'
  }
}

resource generateApiContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: generateApiSt::blobServices
  name: generateApiContainerName
}

resource generateApiAsp 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: generateApiAspName
  location: location
  kind: 'functionapp'
  sku: { name: 'FC1', tier: 'FlexConsumption' }
  properties: { reserved: true }
}

resource generateApiFunc 'Microsoft.Web/sites@2024-11-01' = {
  name: generateApiFuncName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: generateApiAsp.id
    functionAppConfig: {
      runtime: { name: 'python', version: '3.12' }
      scaleAndConcurrency: {
        instanceMemoryMB: 512
        maximumInstanceCount: 40
      }
      deployment: {
        storage: {
          type: 'blobcontainer'
          value: '${generateApiSt.properties.primaryEndpoints.blob}${generateApiContainerName}'
          authentication: { 
            type: 'StorageAccountConnectionString' 
            storageAccountConnectionStringName: 'DEPLOYMENT_STORAGE_CONNECTION_STRING' 
          }
        }
      }
    }
    siteConfig: {
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
          'http://localhost:5173'
          'https://${displayWebStapp.properties.defaultHostname}'
        ]
      }
      appSettings: [
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${generateApiSt.name};AccountKey=${generateApiSt.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'DEPLOYMENT_STORAGE_CONNECTION_STRING', value: 'DefaultEndpointsProtocol=https;AccountName=${generateApiSt.name};AccountKey=${generateApiSt.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: generateApiAppi.properties.ConnectionString }
        { name: 'AZURE_IMGS_STORAGE_CONNECTION_STRING', value: 'DefaultEndpointsProtocol=https;AccountName=${imgsSt.name};AccountKey=${imgsSt.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
      ]
    }
  }
}

// display-web
resource displayWebStapp 'Microsoft.Web/staticSites@2024-11-01' = {
  name: displayWebName
  location: 'eastasia'
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
}

// ----- outputs -----
output generateApiFuncName string = generateApiFunc.name
output imgsStName string = imgsSt.name
output displayWebStappName string = displayWebStapp.name
output generateApiDefaultHostName string = generateApiFunc.properties.defaultHostName
