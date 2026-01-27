# Backend Test Matrix

This document maps each backend component to its test types, runners, and gates.

## Test Layers

| Layer | Speed | AWS Deps | Docker | When Run |
|-------|-------|----------|--------|----------|
| Unit | <10s | None (stubbed) | No | Pre-commit (optional), PR |
| Component | <30s | Mocked (Stubber/Moto) | No | PR |
| Integration (LocalStack) | 2-5min | LocalStack emulation | Yes | Local dev, nightly |
| Integration (Staging E2E) | 5-15min | Real AWS | No | Main branch (pre-prod) |
| Prod Smoke | <1min | Real AWS | No | Post-deploy |
| Synthetics | Continuous | Real AWS | No | Always (CloudWatch) |

## Component → Test Coverage Matrix

### API Lambda (`services/api/handler.py`)

| Test Type | What's Tested | Runner | CI Gate | Staging Gate | Prod Signal |
|-----------|---------------|--------|---------|--------------|-------------|
| Unit | `convert_floats_to_decimal`, `convert_decimal_to_native`, Pydantic schemas | `pytest` | PR | - | - |
| Component | FastAPI routes via `TestClient`, DynamoDB/SQS calls mocked | `pytest` + Moto/Stubber | PR | - | - |
| Integration (Local) | Full API → LocalStack DynamoDB/SQS flow | SAM local + LocalStack | Nightly | - | - |
| Integration (Staging) | Real API Gateway → Lambda → DynamoDB/SQS | `pytest` + `httpx` | - | Main branch | - |
| Prod Smoke | `/api/health` returns 200 | `pytest` or script | - | - | Post-deploy |
| Synthetics | `/api/health` every 5min | CloudWatch Synthetics | - | - | Always |

### Worker Lambda (`services/worker/handler.py`)

| Test Type | What's Tested | Runner | CI Gate | Staging Gate | Prod Signal |
|-----------|---------------|--------|---------|--------------|-------------|
| Unit | `slugify`, `append_event`, `convert_floats_to_decimal` | `pytest` | PR | - | - |
| Component | `handler()` with synthetic SQS events, AWS mocked | `pytest` + Moto/Stubber | PR | - | - |
| Component | `process_job()` with mocked pipeline modules | `pytest` + mocks | PR | - | - |
| Integration (Local) | Worker consumes from LocalStack SQS, writes to S3 | `local_poller.py` + LocalStack | Nightly | - | - |
| Integration (Staging) | Real SQS → Lambda → DynamoDB/S3 | Submit job + poll status | - | Main branch | - |
| Observability | Lambda errors, throttles, duration | CloudWatch Alarms | - | - | Always |

### Core Domain (`paperpilot/core/**`)

| Test Type | What's Tested | Runner | CI Gate | Staging Gate | Prod Signal |
|-----------|---------------|--------|---------|--------------|-------------|
| Unit | ELO calculations, report serialization, models | `pytest` | PR | - | - |
| Unit (async) | `run_search`, `generate_report` with mocked HTTP/OpenAI | `pytest-asyncio` | PR | - | - |
| Property | Edge cases via Hypothesis (optional) | `pytest` + `hypothesis` | PR | - | - |

## Gate Definitions

### Pre-commit (Developer Workstation)
- **Format**: `ruff format --check`
- **Lint**: `ruff check`
- **Type**: `pyright` (scoped to `paperpilot/`, `services/`)
- **Tests**: Optional fast unit subset

### PR / CodeBuild Test Stage
- **All of pre-commit checks**
- **Unit tests**: `pytest tests/unit/ -v`
- **Component tests**: `pytest tests/component/ -v`
- **No Docker, no real AWS**

### Main Branch / Staging E2E
- **Deploy staging stack**: `sam deploy --config-env staging`
- **Run E2E tests**: `pytest tests/e2e/ --env=staging`
- **Assert real AWS side-effects**

### Prod Deploy + Smoke
- **Deploy prod stack**: `sam deploy --config-env prod`
- **Smoke tests**: `pytest tests/smoke/ --env=prod`
- **Verify `/api/health`, optionally tiny job

### Continuous (Synthetics + Alarms)
- CloudWatch Synthetics canary: `/api/health` every 5min
- CloudWatch Alarms:
  - API: 5xx rate, p99 latency
  - Worker: Lambda errors, duration, SQS age-of-oldest-message

## Test File Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_api_helpers.py  # API Lambda helper functions
│   ├── test_worker_helpers.py
│   └── core/
│       ├── test_elo.py
│       ├── test_models.py
│       └── test_report.py
├── component/
│   ├── test_api_routes.py   # FastAPI TestClient + mocked AWS
│   └── test_worker_handler.py
├── integration/
│   └── test_localstack.py   # LocalStack-based tests
├── e2e/
│   └── test_staging.py      # Real AWS staging tests
└── smoke/
    └── test_prod_health.py  # Post-deploy prod checks
```

## Environment Variables for Tests

| Variable | Unit/Component | LocalStack | Staging E2E | Prod Smoke |
|----------|----------------|------------|-------------|------------|
| `AWS_ENDPOINT_URL` | - | `http://localhost:4566` | - | - |
| `JOBS_TABLE_NAME` | mocked | `paperpilot-jobs-prod` | `paperpilot-jobs-staging` | `paperpilot-jobs-prod` |
| `SQS_QUEUE_URL` | mocked | LocalStack URL | staging URL | - |
| `RESULTS_BUCKET` | mocked | `paperpilot-artifacts-local` | staging bucket | - |
| `STAGING_API_URL` | - | - | CloudFormation output | - |
| `PROD_API_URL` | - | - | - | CloudFormation output |
| `OPENAI_API_KEY` | mocked | mocked | real (tiny payload) | - |
