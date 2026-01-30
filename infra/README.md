# Azure Infrastructure (Bicep)

This repo uses **Azure Bicep** to make Azure backend infrastructure **reviewable and reproducible**. The goal is that **PRs are the source of truth**, not ad-hoc portal edits.

## What this manages (Phase 1)

- **Key Vault**: created and used to store secrets (no secrets in git)
- **Function App wiring for secrets**: app settings are switched to **Key Vault references** via CLI (safe, key-by-key updates)
- Existing “heavy” resources are referenced as **existing** (not created/modified yet):
  - Cosmos DB account / database / container
  - Service Bus namespace / queue
  - Storage account / containers

## Deploy (prod)

Prereqs:
- Azure CLI logged in (`az login`)
- Contributor access to resource group `PaperPilot`

Deploy:

```bash
az deployment group create \
  -g PaperPilot \
  -f infra/main.bicep \
  -p infra/params/prod.bicepparam
```

## Secrets flow (Key Vault references)

This project uses App Service **Key Vault references** for sensitive settings. The pattern is:

- You **store** the secret in Key Vault (one-time / when rotating)
- The Function App setting value becomes a reference like:
  - `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/<version>)`

Docs: `https://learn.microsoft.com/en-us/azure/app-service/app-service-key-vault-references`

### One-time setup

1) Deploy infra to create the Key Vault.
2) Ensure the Function App has an identity and access to read secrets.
3) Populate Key Vault secrets.
4) Update the Function App app settings to point to Key Vault references.

This repo’s default production wiring (Resource Group `PaperPilot`) uses:

- **Function App**: `paperpilot-api`
- **Key Vault**: `paperpilot-kv-prod`
- **User-assigned identity**: `paperpilot-api-id-97d1`

### Secret names (prod)

These Key Vault secrets are expected (names are case-sensitive):

- `OPENAI-API-KEY` → `OPENAI_API_KEY`
- `AZURE-COSMOS-KEY` → `AZURE_COSMOS_KEY`
- `AZURE-SERVICE-BUS-CONNECTION-STRING` → `AZURE_SERVICE_BUS_CONNECTION_STRING`
- `AZURE-WEBJOBS-STORAGE` → `AzureWebJobsStorage`

Note: we intentionally **do not** move `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` into Key Vault, because it is part of the Azure Files content mount configuration and is riskier to change.

### Useful CLI snippets (prod)

Populate secrets (values are sourced from existing app settings; nothing is committed to git):

```bash
RG="PaperPilot"
FUNC_APP="paperpilot-api"
KV_NAME="paperpilot-kv-prod"

OPENAI_API_KEY="$(az functionapp config appsettings list -g "$RG" -n "$FUNC_APP" --query "[?name=='OPENAI_API_KEY'].value | [0]" -o tsv)"
az keyvault secret set --vault-name "$KV_NAME" --name "OPENAI-API-KEY" --value "$OPENAI_API_KEY" -o none
```

Switch app settings to Key Vault references:

```bash
KV_URI="https://paperpilot-kv-prod.vault.azure.net"
az functionapp config appsettings set -g PaperPilot -n paperpilot-api --settings \
  "OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=${KV_URI}/secrets/OPENAI-API-KEY)"
```

## Drift policy (important)

- **No portal edits for app settings / infra wiring**.
- If you must do an emergency portal edit, follow up with a PR that updates Bicep/workflows the same day.

## Phase 2 (later)

- Export your full resource group and decompile into Bicep, then refactor into modules.
- Move Cosmos/ServiceBus/Storage from `existing` references to fully managed resources.

