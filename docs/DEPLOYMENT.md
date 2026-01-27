# PaperPilot Serverless Deployment Guide

This guide covers deploying PaperPilot to AWS using SAM (Serverless Application Model) and CodePipeline.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│ CodePipeline│────▶│  CodeBuild  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  SAM Deploy │
                                        └─────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
            │ API Gateway │            │  DynamoDB   │            │     SQS     │
            │   (HTTP)    │            │ (Jobs Table)│            │   (Queue)   │
            └─────────────┘            └─────────────┘            └─────────────┘
                    │                          │                          │
                    ▼                          │                          │
            ┌─────────────┐                    │                          │
            │ API Lambda  │◀───────────────────┤                          │
            │  (FastAPI)  │                    │                          │
            └─────────────┘                    │                          │
                    │                          │                          │
                    │ (enqueue)                │                          │
                    ▼                          │                          │
                   SQS ────────────────────────┼──────────────────────────┘
                    │                          │
                    │ (trigger)                │
                    ▼                          │
            ┌─────────────┐                    │
            │   Worker    │◀───────────────────┘
            │   Lambda    │ (update status)
            └─────────────┘
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **SAM CLI** installed (`pip install aws-sam-cli`)
3. **Docker** installed (for `sam build --use-container`)
4. **Python 3.13** (or use container builds)

## Local Development

The local development environment mirrors the production AWS setup as closely as possible using:

- **SAM CLI** - Runs Lambda functions locally with API Gateway emulation
- **LocalStack** - Emulates DynamoDB and SQS locally
- **Local Worker Poller** - Polls SQS and invokes the worker handler

### Prerequisites

1. **Docker** - Required for LocalStack and SAM local
   ```bash
   docker --version  # Should be 20.10+
   ```

2. **SAM CLI** - AWS Serverless Application Model CLI
   ```bash
   pip install aws-sam-cli
   sam --version  # Should be 1.100+
   ```

3. **AWS CLI** - For verifying LocalStack resources (optional but helpful)
   ```bash
   pip install awscli
   aws --version
   ```

4. **Node.js** - For the frontend
   ```bash
   node --version  # Should be 18+
   ```

5. **tmux** - For the unified dev environment
   ```bash
   # macOS
   brew install tmux
   
   # Ubuntu/Debian
   sudo apt install tmux
   ```

### Quick Start

The easiest way to start the full local environment:

```bash
# Start everything: LocalStack, SAM API, Worker, Frontend
make dev

# This opens a tmux session with 4 panes:
# - LocalStack logs
# - SAM local API (port 8000)
# - Worker poller
# - Frontend (port 5173)
```

To stop everything:

```bash
make dev-stop
```

### Individual Components

You can also run components individually for debugging:

```bash
# 1. Start LocalStack (DynamoDB + SQS)
make dev-infra

# 2. Build SAM application
make dev-sam-build

# 3. Start SAM local API (in a separate terminal)
make dev-api

# 4. Start worker poller (in a separate terminal)
make dev-worker

# 5. Start frontend (in a separate terminal)
make frontend
```

### Verify Local Setup

```bash
# Check LocalStack status and resources
make dev-check

# Test the API health endpoint
curl http://localhost:8000/api/health

# Create a test job
curl -X POST http://localhost:8000/api/pipeline \
  -H "Content-Type: application/json" \
  -d '{"query": "Test Query"}'

# Check DynamoDB tables
aws --endpoint-url http://localhost:4566 dynamodb list-tables --region eu-central-1

# Check SQS queues
aws --endpoint-url http://localhost:4566 sqs list-queues --region eu-central-1
```

### Architecture (Local)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Local Development                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐          ┌────────────────────────────────┐   │
│  │   Frontend   │──────────│    SAM Local API (port 8000)   │   │
│  │ (port 5173)  │          │    (Lambda + API Gateway)      │   │
│  └──────────────┘          └────────────────────────────────┘   │
│                                       │                          │
│                                       │ enqueue                  │
│                                       ▼                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   LocalStack (port 4566)                    │ │
│  │  ┌────────────────┐          ┌────────────────────────┐    │ │
│  │  │   DynamoDB     │          │         SQS            │    │ │
│  │  │ (jobs table)   │          │    (jobs queue)        │    │ │
│  │  └────────────────┘          └────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                       │                          │
│                                       │ poll                     │
│                                       ▼                          │
│                          ┌────────────────────────┐              │
│                          │   Local Worker Poller  │              │
│                          │   (Python process)     │              │
│                          └────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Environment Variables (Local)

The local environment uses these settings (set automatically by `make dev`):

| Variable | Local Value | Description |
|----------|-------------|-------------|
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | LocalStack endpoint |
| `JOBS_TABLE_NAME` | `paperpilot-jobs-prod` | DynamoDB table name |
| `SQS_QUEUE_URL` | `http://localhost:4566/000000000000/paperpilot-jobs-prod` | SQS queue URL |
| `AWS_DEFAULT_REGION` | `eu-central-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | `test` | Dummy credentials for LocalStack |
| `AWS_SECRET_ACCESS_KEY` | `test` | Dummy credentials for LocalStack |
| `LOG_LEVEL` | `DEBUG` | Verbose logging for debugging |

### Files Overview

| File | Purpose |
|------|---------|
| `infra/docker-compose.local.yml` | Docker Compose for LocalStack |
| `infra/init-localstack/01-init-aws-resources.sh` | Auto-creates DynamoDB table + SQS queue |
| `infra/env.local.json` | Environment variables for SAM local |
| `services/worker/local_poller.py` | SQS poller that invokes worker handler |

### Troubleshooting (Local)

#### LocalStack not starting

```bash
# Check Docker is running
docker ps

# Check LocalStack logs
docker-compose -f infra/docker-compose.local.yml logs

# Restart LocalStack
make dev-infra-stop && make dev-infra
```

#### SAM local API errors

```bash
# Make sure LocalStack is running first
make dev-check

# Rebuild SAM application
make dev-sam-build

# Check SAM local is using the right env vars
cat infra/env.local.json
```

#### "Queue does not exist" error

```bash
# The init script should create the queue automatically
# If it didn't, check LocalStack logs:
docker-compose -f infra/docker-compose.local.yml logs localstack

# Manually create the queue:
aws --endpoint-url http://localhost:4566 sqs create-queue \
  --queue-name paperpilot-jobs-prod \
  --region eu-central-1
```

#### Port 8000 already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or use a different port
SAM_PORT=3000 make dev-api
```

#### Worker not processing messages

```bash
# Check if messages are in the queue
aws --endpoint-url http://localhost:4566 sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/paperpilot-jobs-prod \
  --attribute-names ApproximateNumberOfMessages \
  --region eu-central-1

# Check worker poller logs for errors
# The poller should print each message it receives
```

### Hot Reload Limitations

- **Frontend**: Full hot reload via Vite
- **SAM Local API**: Partial hot reload - code changes are picked up, but heavy changes may require `make dev-sam-build`
- **Worker Poller**: Requires restart on code changes (Ctrl+C and `make dev-worker`)

For faster iteration on Lambda code, consider running the FastAPI app directly with uvicorn:

```bash
# Direct FastAPI (without Lambda/SAM wrapper)
make api
```

## Manual Deployment

### First-time Setup

1. **Create the OpenAI API key in SSM Parameter Store:**

```bash
aws ssm put-parameter \
  --name /paperpilot/openai-api-key \
  --value "sk-proj-YOUR_API_KEY_HERE" \
  --type SecureString \
  --region eu-central-1
```

1. **Deploy the stack:**

```bash
cd infra

# Copy paperpilot package
cp -r ../paperpilot ../services/api/
cp -r ../paperpilot ../services/worker/

# Build
sam build --use-container

# Deploy (first time - will prompt for parameters)
sam deploy --guided

# Subsequent deploys
sam deploy
```

### Deploy to Different Environments

```bash
# Deploy to dev
sam deploy --config-env dev

# Deploy to staging
sam deploy --config-env staging

# Deploy to prod (default)
sam deploy --config-env prod
```

## AWS CodePipeline Setup

### Step 1: Create GitHub Connection

1. Go to **AWS Console > Developer Tools > Settings > Connections**
2. Click **Create connection**
3. Select **GitHub** as the provider
4. Name it `paperpilot-github`
5. Click **Connect to GitHub** and authorize AWS
6. Select your GitHub account/organization
7. Click **Connect**

### Step 2: Create CodeBuild Project

1. Go to **AWS Console > CodeBuild > Build projects**
2. Click **Create build project**
3. Configure:
   - **Project name:** `paperpilot-build`
   - **Source:** GitHub (via connection)
   - **Repository:** Select your PaperPilot repo
   - **Environment:**
     - **Image:** `aws/codebuild/amazonlinux2-x86_64-standard:5.0`
     - **Privileged:** Yes (for Docker/SAM container builds)
     - **Service role:** Create new or use existing
   - **Buildspec:** Use buildspec file (`buildspec.yml`)
4. Click **Create build project**

### Step 3: Add IAM Permissions to CodeBuild Role

The CodeBuild service role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "dynamodb:*",
        "sqs:*",
        "iam:*",
        "logs:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:eu-central-1:*:parameter/paperpilot/*"
    }
  ]
}
```

### Step 4: Create CodePipeline

1. Go to **AWS Console > CodePipeline > Pipelines**
2. Click **Create pipeline**
3. Choose **Build custom pipeline** (V2)
4. Configure:
   - **Pipeline name:** `paperpilot-deploy`
   - **Pipeline type:** V2
   - **Service role:** Create new or use existing

5. **Source stage:**
   - **Source provider:** GitHub (Version 2)
   - **Connection:** Select your GitHub connection
   - **Repository:** Select PaperPilot
   - **Branch:** `main` (or your deployment branch)
   - **Output artifact format:** CodePipeline default

6. **Build stage:**
   - **Build provider:** AWS CodeBuild
   - **Project name:** `paperpilot-build`

7. **Deploy stage:**
   - **Skip** (SAM deploy is handled in CodeBuild)

8. Click **Create pipeline**

### Step 5: Add Lambda Environment Variables

After the first deployment, add the OpenAI API key to Lambda:

1. Go to **Lambda Console**
2. Select `paperpilot-api-prod`
3. Go to **Configuration > Environment variables**
4. Add: `OPENAI_API_KEY` = your key (or reference SSM)

Repeat for `paperpilot-worker-prod`.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls | Yes |
| `JOBS_TABLE_NAME` | DynamoDB table name (auto-set by SAM) | No |
| `SQS_QUEUE_URL` | SQS queue URL (auto-set by SAM) | No |
| `RESULTS_BUCKET` | S3 bucket for pipeline artifacts (auto-set by SAM) | No |
| `ENVIRONMENT` | Environment name (dev/staging/prod) | No |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/WARNING) | No |
| `AWS_ENDPOINT_URL` | Custom AWS endpoint for LocalStack (local dev only) | No |

## S3 Artifacts

Pipeline results are stored in S3 under a structured prefix:

```
s3://paperpilot-artifacts-{environment}-{account-id}/
└── results/
    └── {query_slug}/
        └── {job_id}/
            ├── metadata.json      # Index of all artifacts
            ├── snowball.json      # Search results (all papers found)
            ├── elo_ranked_*.json  # Ranked papers with ELO scores
            └── report_top_k*.json # Generated research report
```

### Inspecting Artifacts (Prod)

```bash
# List all results for a query
aws s3 ls s3://paperpilot-artifacts-prod-<account-id>/results/<query_slug>/

# Download a specific job's artifacts
aws s3 sync s3://paperpilot-artifacts-prod-<account-id>/results/<query_slug>/<job-id>/ ./local-results/

# View metadata for a job
aws s3 cp s3://paperpilot-artifacts-prod-<account-id>/results/<query_slug>/<job-id>/metadata.json -
```

### Inspecting Artifacts (Local Dev)

```bash
# List buckets
aws --endpoint-url http://localhost:4566 s3 ls

# List results
aws --endpoint-url http://localhost:4566 s3 ls s3://paperpilot-artifacts-local/results/ --recursive

# Download a job's results
aws --endpoint-url http://localhost:4566 s3 sync \
  s3://paperpilot-artifacts-local/results/<query_slug>/<job-id>/ ./local-results/
```

## Job Progress and Events

The pipeline updates DynamoDB with progress information that can be used by frontends for real-time updates.

### Progress Model

Each job has these fields in DynamoDB:

| Field | Description |
|-------|-------------|
| `status` | `queued`, `running`, `completed`, or `failed` |
| `progress` | Current progress snapshot: `{phase, step, message, current, total}` |
| `events` | Bounded list (last 100) of progress events for replay |
| `result` | On completion: summary + S3 pointers |
| `error_message` | On failure: error details |

### Progress Phases

The pipeline progresses through these phases:

1. **search** - Query profile, arXiv search, filtering, snowball expansion
2. **ranking** - ELO-based pairwise paper ranking
3. **report** - Paper cards, outline, section writing, auditing
4. **upload** - Upload artifacts to S3

### Events List (for Real-Time UX)

The `events` field contains an append-only list (bounded to last 100 events):

```json
{
  "events": [
    {"ts": "2026-01-27T10:00:00Z", "type": "phase_start", "phase": "search", "message": "Starting search..."},
    {"ts": "2026-01-27T10:00:05Z", "type": "progress", "phase": "search", "message": "Found 50 papers", "step": 2},
    {"ts": "2026-01-27T10:01:00Z", "type": "phase_complete", "phase": "search", "message": "Search complete: 150 papers"},
    {"ts": "2026-01-27T10:01:01Z", "type": "phase_start", "phase": "ranking", "message": "Starting ranking..."},
    ...
  ]
}
```

### Polling for Progress

Frontend can poll `GET /api/jobs/{job_id}` to get current status:

```bash
# Check job status
curl https://<api-url>/api/jobs/<job-id>

# Response includes progress and events
{
  "job_id": "abc-123",
  "status": "running",
  "progress": {
    "phase": "ranking",
    "step": 1,
    "message": "Running ELO matches...",
    "current": 25,
    "total": 100
  },
  "events": [...],
  "result": null
}
```

### Future: Real-Time Streaming

The events model is designed so that later you can add SSE/WebSocket streaming without changing the worker. The worker writes events to DynamoDB; a streaming API can then watch for changes and push them to clients.

## Monitoring

### CloudWatch Logs

- API logs: `/aws/lambda/paperpilot-api-prod`
- Worker logs: `/aws/lambda/paperpilot-worker-prod`

### CloudWatch Metrics

Key metrics to monitor:

- `Invocations` - Number of Lambda invocations
- `Duration` - Execution time
- `Errors` - Failed invocations
- `Throttles` - Rate-limited invocations

### X-Ray Tracing (Optional)

Enable X-Ray tracing in the SAM template for distributed tracing.

## Troubleshooting

### Build Fails

1. Check CodeBuild logs for errors
2. Ensure Docker is enabled for container builds
3. Verify Python version matches Lambda runtime

### Deploy Fails

1. Check CloudFormation events for errors
2. Verify IAM permissions for CodeBuild role
3. Check that all parameters are correctly set

### Lambda Errors

1. Check CloudWatch Logs for the function
2. Verify environment variables are set
3. Check Lambda timeout and memory settings

### SQS Not Triggering Worker

1. Verify event source mapping is active
2. Check SQS queue permissions
3. Verify Lambda has `sqs:ReceiveMessage` permission

## Cost Optimization

1. **DynamoDB:** Using PAY_PER_REQUEST for variable workloads
2. **Lambda:** Adjust memory based on actual usage
3. **Worker Concurrency:** Limited to 5 to avoid API rate limits
4. **TTL:** Jobs auto-expire after 7 days

## Security Best Practices

1. Store API keys in SSM Parameter Store or Secrets Manager
2. Use IAM roles with least-privilege permissions
3. Enable encryption at rest for DynamoDB
4. Enable VPC for Lambda if accessing private resources
5. Use API Gateway authorization for production
