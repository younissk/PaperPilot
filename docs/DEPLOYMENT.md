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

### Install SAM CLI

```bash
pip install aws-sam-cli
sam --version
```

### Build Locally

```bash
# Navigate to infra directory
cd infra

# Copy paperpilot package to services (needed for SAM)
cp -r ../paperpilot ../services/api/
cp -r ../paperpilot ../services/worker/

# Build with container (recommended for consistent builds)
sam build --use-container

# Or build natively (requires Python 3.13)
sam build
```

### Test Locally

```bash
# Start local API Gateway + Lambda
cd infra
sam local start-api

# The API will be available at http://127.0.0.1:3000

# Test health endpoint
curl http://127.0.0.1:3000/api/health

# Invoke a single function
sam local invoke ApiFunction --event events/api-event.json

# Invoke worker with SQS event
sam local invoke WorkerFunction --event events/sqs-event.json
```

### Local DynamoDB (Optional)

For testing DynamoDB locally:

```bash
# Start local DynamoDB
docker run -p 8000:8000 amazon/dynamodb-local

# Set endpoint for local testing
export AWS_SAM_LOCAL=true
export DYNAMODB_ENDPOINT=http://localhost:8000
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
| `ENVIRONMENT` | Environment name (dev/staging/prod) | No |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/WARNING) | No |

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
