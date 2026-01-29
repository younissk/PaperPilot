# PaperPilot

AI-powered academic literature discovery using snowball sampling, ELO ranking, and LLM-generated research reports.

## Overview

PaperPilot helps researchers discover relevant academic papers by:

1. **Snowball Sampling**: Starting from seed papers, it explores citations and references to find related work
2. **LLM-Based Filtering**: Uses GPT to filter papers for relevance to your research query
3. **ELO Ranking**: Compares papers head-to-head using LLM judgment to create a quality ranking
4. **Report Generation**: Synthesizes findings into a structured research report

## Architecture (Azure)

PaperPilot runs as a serverless backend on Azure:

```
┌────────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│  React/Vite Frontend       │────▶│  Azure Functions API     │────▶│  Azure Functions Worker  │
│  (Static Web App)          │     │  (HTTP triggers)         │     │  (Service Bus trigger)   │
└────────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
                                        │            │                         │
                                        │            │                         ▼
                                        │            └───────────────┐  ┌──────────────────────┐
                                        ▼                            └▶│  Azure Service Bus   │
                               ┌──────────────────────┐                │  (Job queue)         │
                               │  Azure Cosmos DB     │                └──────────────────────┘
                               │  (Job state/events)  │
                               └──────────────────────┘
                                        │
                                        ▼
                               ┌──────────────────────┐
                               │  Azure Blob Storage  │
                               │  (Artifacts/results) │
                               └──────────────────────┘
```

### Components

- **Frontend** (`frontend/`): React/Vite app for the web interface
- **Azure Functions** (`azure-functions/`): HTTP API + Service Bus worker
- **Core Library** (`paperpilot/`): Shared domain logic (search, ranking, reports)
- **CLI** (`paperpilot/cli/`): Command-line interface for local usage

## Quick Start

### Option 1: CLI (Simplest)

```bash
# Install dependencies
uv sync

# Run a search
uv run paperpilot search "LLM Based Recommendation Systems" -n 30

# View results
uv run paperpilot results snowball_results.json
```

### Option 2: Frontend Dev

```bash
cd frontend
npm install
npm run dev
```

### Option 3: Azure Functions Local (optional)

If you have Azure Functions Core Tools installed:

```bash
cd azure-functions
func start
```

## Project Structure

```
PaperPilot/
├── azure-functions/      # Azure Functions entrypoint + modules
├── frontend/             # React/Vite frontend
├── paperpilot/           # Core library (domain logic)
│   ├── api/              # Legacy monolith API (deprecated)
│   ├── cli/              # CLI commands
│   └── core/             # Search, ranking, reports
├── tests/                # Test suites
└── results/              # Example outputs (historical)
```

## Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for Python package management
- Node.js 18+ (for frontend)
- Azure Functions Core Tools (optional, for local Functions)

### Setup

```bash
# Install Python dependencies (including test/dev extras)
uv sync --extra test --extra dev

# Install pre-commit hooks
pre-commit install

# Install frontend dependencies
cd frontend && npm install
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=paperpilot
```

### Code Quality

```bash
# Format code
uv run ruff format paperpilot tests azure-functions

# Lint
uv run ruff check paperpilot tests azure-functions

# Type check
uv run pyright
```

## Deployment

- **Frontend**: GitHub Actions deploys to Azure Static Web Apps (`.github/workflows/azure-static-web-apps.yml`)
- **Backend**: GitHub Actions deploys Azure Functions (`.github/workflows/azure-functions-deploy.yml`)

## Configuration

### Environment Variables (Azure Functions)

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes (or Key Vault) |
| `AZURE_COSMOS_ENDPOINT` | Cosmos DB endpoint | Yes |
| `AZURE_COSMOS_KEY` | Cosmos DB key | Yes |
| `AZURE_COSMOS_DATABASE` | Cosmos DB database name | Yes |
| `AZURE_COSMOS_CONTAINER` | Cosmos DB container name | Yes |
| `AZURE_SERVICE_BUS_CONNECTION_STRING` | Service Bus connection string | Yes |
| `AZURE_SERVICE_BUS_QUEUE_NAME` | Service Bus queue name | Yes |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob storage connection string | Yes |
| `AZURE_RESULTS_CONTAINER` | Blob container for results | Yes |
| `AZURE_RESULTS_PREFIX` | Blob prefix for results | No |
| `AZURE_KEY_VAULT_URL` | Key Vault URL (optional) | No |
| `OPENAI_API_KEY_SECRET_NAME` | Key Vault secret name (optional) | No |

## API Endpoints

- `POST /api/pipeline` - Start a pipeline job
- `GET /api/pipeline/{job_id}` - Get job status
- `GET /api/jobs/{job_id}` - Raw job status
- `GET /api/jobs/{job_id}/events` - Job event log
- `GET /api/results` - List completed queries
- `GET /api/results/{query}/all` - Get all results for a query

## License

[Add license here]

## Contributing

[Add contributing guidelines here]
