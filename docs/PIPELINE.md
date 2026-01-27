# CodePipeline Setup Guide

This document describes how to set up the CI/CD pipeline for PaperPilot using AWS CodePipeline and CodeBuild.

## Pipeline Architecture

```
GitHub (Source)
    │
    ▼
┌─────────────────┐
│   Test Stage    │  ◀── buildspec.test.yml
│  (CodeBuild)    │      - Format/lint/type checks
│                 │      - Unit tests
│                 │      - Component tests
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy Staging  │  ◀── buildspec.deploy-staging.yml
│  (CodeBuild)    │      - SAM build
│                 │      - SAM deploy (staging)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Staging E2E     │  ◀── buildspec.e2e-staging.yml
│  (CodeBuild)    │      - E2E tests against real AWS
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Manual Approval │  (Optional but recommended)
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy Prod    │  ◀── buildspec.deploy-prod.yml
│  (CodeBuild)    │      - SAM build
│                 │      - SAM deploy (prod)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prod Smoke     │  ◀── buildspec.smoke-prod.yml
│  (CodeBuild)    │      - Health checks
│                 │      - Basic endpoint tests
└─────────────────┘
```

## Prerequisites

### 1. SQS Queues (Pre-create)

The pipeline expects SQS queues to exist. Create them manually or via a separate stack:

```bash
# Staging queue
aws sqs create-queue --queue-name paperpilot-jobs-staging --region eu-central-1

# Production queue (if not exists)
aws sqs create-queue --queue-name paperpilot-jobs-prod --region eu-central-1
```

### 2. GitHub Connection

Create a CodeStar connection to GitHub:
1. Go to AWS Console → Developer Tools → Connections
2. Create connection to GitHub
3. Note the connection ARN

### 3. IAM Roles

The pipeline needs roles with permissions for:
- CodeBuild: CloudFormation, S3, Lambda, DynamoDB, SQS, API Gateway, IAM
- CodePipeline: S3, CodeBuild, CodeStar connections

## Creating the Pipeline

### Option A: AWS Console

1. **Create Pipeline**
   - Name: `paperpilot-pipeline`
   - Service role: Create new or use existing

2. **Source Stage**
   - Provider: GitHub (via CodeStar connection)
   - Repository: `your-org/PaperPilot`
   - Branch: `main`
   - Output artifact: `SourceArtifact`

3. **Test Stage**
   - Action: CodeBuild
   - Project: Create new
   - Buildspec: `buildspec.test.yml`
   - Environment: Ubuntu, Standard 7.0, Python 3.13

4. **Deploy Staging Stage**
   - Action: CodeBuild
   - Project: Create new
   - Buildspec: `buildspec.deploy-staging.yml`
   - Environment: Ubuntu, Standard 7.0, Python 3.13, Privileged (for Docker)

5. **Staging E2E Stage**
   - Action: CodeBuild
   - Project: Create new
   - Buildspec: `buildspec.e2e-staging.yml`
   - Environment: Ubuntu, Standard 7.0, Python 3.13

6. **Manual Approval** (Optional)
   - Action: Manual approval
   - SNS topic for notifications (optional)

7. **Deploy Prod Stage**
   - Action: CodeBuild
   - Project: Create new
   - Buildspec: `buildspec.deploy-prod.yml`
   - Environment: Ubuntu, Standard 7.0, Python 3.13, Privileged (for Docker)

8. **Prod Smoke Stage**
   - Action: CodeBuild
   - Project: Create new
   - Buildspec: `buildspec.smoke-prod.yml`
   - Environment: Ubuntu, Standard 7.0, Python 3.13

### Option B: CloudFormation

Use the template in `infra/pipeline.yaml` (see below).

## Environment Variables

### Test Stage
- `AWS_ACCESS_KEY_ID`: `testing` (fake, for mocked tests)
- `AWS_SECRET_ACCESS_KEY`: `testing`
- `AWS_DEFAULT_REGION`: `eu-central-1`

### Deploy Stages
- Default AWS credentials from CodeBuild service role
- `SAM_CLI_TELEMETRY`: `0`

### E2E/Smoke Stages
- `STAGING_API_URL` / `PROD_API_URL`: Retrieved from CloudFormation outputs

## Troubleshooting

### Common Issues

1. **SAM build fails with Docker errors**
   - Ensure CodeBuild project has "Privileged" mode enabled
   - Check Docker daemon is running

2. **Deploy fails with IAM errors**
   - Verify CodeBuild role has `iam:CreateRole`, `iam:AttachRolePolicy` permissions
   - Check `CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM` are set

3. **E2E tests fail to connect**
   - Verify staging stack deployed successfully
   - Check API Gateway URL is correctly captured
   - Ensure CodeBuild has network access to API Gateway

4. **Tests timeout**
   - Increase CodeBuild timeout (default 60 minutes)
   - For E2E tests, consider increasing HTTP client timeout

## Local Testing of Pipeline Steps

Test each buildspec locally before pushing:

```bash
# Test stage (unit + component tests)
make ci-check

# Simulate staging deploy (requires AWS credentials)
cd infra && sam build && sam deploy --config-env staging

# E2E tests (requires STAGING_API_URL)
export STAGING_API_URL=https://xxx.execute-api.eu-central-1.amazonaws.com
pytest tests/e2e/ -v -m "e2e and not slow"

# Smoke tests (requires PROD_API_URL)
export PROD_API_URL=https://xxx.execute-api.eu-central-1.amazonaws.com
pytest tests/smoke/ -v -m "smoke and not optional"
```

## Cost Considerations

- **CodeBuild**: Charged per build minute
- **Staging Stack**: Running Lambda functions, DynamoDB, S3 (minimal cost when idle)
- **E2E Tests**: May incur OpenAI API costs if using real keys
- **Tip**: Use minimal test payloads (`num_results=1`, `max_iterations=1`)

## Rollback Strategy

If production smoke tests fail:

1. **Automatic**: Configure CloudFormation to rollback on failure
2. **Manual**: Use CloudFormation console to rollback to previous version
3. **Blue/Green**: Consider deploying to a separate stack and swapping

```bash
# Manual rollback
aws cloudformation rollback-stack --stack-name paperpilot
```
