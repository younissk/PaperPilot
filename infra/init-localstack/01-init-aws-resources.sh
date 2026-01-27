#!/bin/bash
# LocalStack init script - runs when LocalStack becomes ready
# Creates DynamoDB table, SQS queue, and S3 bucket for local development
#
# This script auto-creates the same resources that exist in prod,
# allowing local development to mirror the production environment.

set -e

echo "=== PaperPilot LocalStack Initialization ==="

REGION="eu-central-1"
TABLE_NAME="paperpilot-jobs-prod"
QUEUE_NAME="paperpilot-jobs-prod"
BUCKET_NAME="paperpilot-artifacts-local"

# Wait for LocalStack to be fully ready
echo "Waiting for LocalStack services..."
sleep 2

# Create DynamoDB table (matches template.yaml JobsTable)
echo "Creating DynamoDB table: $TABLE_NAME"
awslocal dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=job_id,AttributeType=S \
    --key-schema AttributeName=job_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION" \
    2>/dev/null || echo "Table $TABLE_NAME already exists or creation failed"

# Verify table exists
echo "Verifying DynamoDB table..."
awslocal dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" \
    --query 'Table.TableStatus' --output text

# Create SQS queue (matches the existing prod queue)
echo "Creating SQS queue: $QUEUE_NAME"
awslocal sqs create-queue \
    --queue-name "$QUEUE_NAME" \
    --region "$REGION" \
    2>/dev/null || echo "Queue $QUEUE_NAME already exists or creation failed"

# Get and display queue URL
QUEUE_URL=$(awslocal sqs get-queue-url --queue-name "$QUEUE_NAME" --region "$REGION" --query 'QueueUrl' --output text)
echo "Queue URL: $QUEUE_URL"

# Create S3 bucket for artifacts (matches template.yaml ArtifactsBucket)
echo "Creating S3 bucket: $BUCKET_NAME"
awslocal s3 mb "s3://$BUCKET_NAME" --region "$REGION" \
    2>/dev/null || echo "Bucket $BUCKET_NAME already exists or creation failed"

# Verify bucket exists
echo "Verifying S3 bucket..."
awslocal s3 ls "s3://$BUCKET_NAME" --region "$REGION" 2>/dev/null && echo "Bucket exists" || echo "Bucket empty (OK)"

echo ""
echo "=== LocalStack Initialization Complete ==="
echo "DynamoDB Table: $TABLE_NAME"
echo "SQS Queue: $QUEUE_NAME"
echo "SQS Queue URL: $QUEUE_URL"
echo "S3 Bucket: $BUCKET_NAME"
echo ""
echo "You can verify with:"
echo "  aws --endpoint-url http://localhost:4566 dynamodb list-tables --region $REGION"
echo "  aws --endpoint-url http://localhost:4566 sqs list-queues --region $REGION"
echo "  aws --endpoint-url http://localhost:4566 s3 ls --region $REGION"
echo ""
