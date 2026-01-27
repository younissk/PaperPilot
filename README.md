# PaperPilot

AI-powered academic literature discovery using snowball sampling, ELO ranking, and LLM-generated research reports.

## Overview

PaperPilot helps researchers discover relevant academic papers by:

1. **Snowball Sampling**: Starting from seed papers, it explores citations and references to find related work
2. **LLM-Based Filtering**: Uses GPT to filter papers for relevance to your research query
3. **ELO Ranking**: Compares papers head-to-head using LLM judgment to create a quality ranking
4. **Report Generation**: Synthesizes findings into a structured research report

## Architecture

PaperPilot uses a **serverless-first architecture** deployed on AWS:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Astro Frontend │────▶│    API Lambda   │────▶│   Worker Lambda │
│   (SSR on AWS)  │     │    (FastAPI)    │     │  (Pipeline Jobs)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │    DynamoDB     │     │       S3        │
                        │   (Job State)   │     │   (Artifacts)   │
                        └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │      SQS        │
                        │  (Job Queue)    │
                        └─────────────────┘
```

### Components

- **Frontend** (`frontend/`): Astro SSR app for the web interface
- **API Lambda** (`services/api/`): FastAPI for job creation and status queries
- **Worker Lambda** (`services/worker/`): Processes search/rank/report jobs from SQS
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

### Option 2: Local Serverless Development

This mirrors the production AWS setup using LocalStack:

```bash
# Start full local environment (LocalStack + SAM API + Worker + Frontend)
make dev

# This opens a tmux session with:
# - LocalStack (DynamoDB + SQS + S3)
# - SAM local API on port 8000
# - Worker poller
# - Frontend on port 5173
```

To stop:
```bash
make dev-stop
```

### Option 3: Direct API Server (Legacy)

```bash
# Run FastAPI server directly (no AWS emulation)
make api

# In another terminal, run the frontend
make frontend
```

## Project Structure

```
PaperPilot/
├── paperpilot/          # Core library (domain logic)
│   ├── api/             # Legacy monolith API (deprecated)
│   ├── aws/             # Shared AWS utilities
│   ├── cli/             # CLI commands
│   └── core/            # Search, ranking, reports
├── services/            # Lambda entrypoints
│   ├── api/             # API Lambda (job creation, status)
│   └── worker/          # Worker Lambda (pipeline processing)
├── frontend/            # Astro SSR frontend
├── infra/               # SAM templates and local dev config
├── tests/               # Test suites
├── docs/                # Documentation
└── results/             # Example outputs (historical)
```

## Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for Python package management
- Docker (for LocalStack and SAM local)
- Node.js 18+ (for frontend)
- AWS SAM CLI (for local Lambda emulation)

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

# Run by category
uv run pytest -m unit          # Fast unit tests
uv run pytest -m component     # Tests with mocked AWS
uv run pytest -m integration   # Tests requiring LocalStack

# Run with coverage
uv run pytest --cov=paperpilot --cov=services
```

### Code Quality

```bash
# Format code
uv run ruff format paperpilot services tests

# Lint
uv run ruff check paperpilot services tests

# Type check
uv run pyright
```

## Deployment

PaperPilot uses AWS SAM for deployment via CodePipeline:

1. **Test Stage**: Runs linting, type checks, unit and component tests
2. **Deploy Staging**: Builds and deploys to staging environment
3. **E2E Tests**: Runs integration tests against staging
4. **Manual Approval**: (Optional) Human gate before production
5. **Deploy Production**: Deploys to production
6. **Smoke Tests**: Verifies production health

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes |
| `AWS_ENDPOINT_URL` | LocalStack URL for local dev | Local only |
| `JOBS_TABLE_NAME` | DynamoDB table name | Lambda |
| `SQS_QUEUE_URL` | SQS queue URL | Lambda |
| `RESULTS_BUCKET` | S3 bucket for artifacts | Lambda |

### API Configuration

The frontend connects to the API via `API_BASE_URL`:
- Local: `http://localhost:8000`
- Production: Set in Lambda environment

## API Documentation

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for the API contract between frontend and backend.

Key endpoints:
- `POST /api/pipeline` - Start a pipeline job
- `GET /api/pipeline/{job_id}` - Get job status
- `GET /api/results` - List completed queries
- `GET /api/results/{query}/all` - Get all results for a query

## License

[Add license here]

## Contributing

[Add contributing guidelines here]
