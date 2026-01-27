"""Integration tests using LocalStack for AWS service emulation.

These tests require LocalStack to be running:
    make dev-infra

Run with:
    pytest tests/integration/ -v -m integration
"""

import json
import os
import time

import boto3
import pytest
from botocore.config import Config

# Mark all tests in this module as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AWS_ENDPOINT_URL"),
        reason="AWS_ENDPOINT_URL not set (LocalStack not configured)"
    ),
]


@pytest.fixture(scope="module")
def localstack_config():
    """Configuration for LocalStack connection."""
    return {
        "endpoint_url": os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566"),
        "region": os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"),
        "table_name": os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod"),
        "queue_url": os.environ.get(
            "SQS_QUEUE_URL",
            "http://localhost:4566/000000000000/paperpilot-jobs-prod"
        ),
        "bucket_name": os.environ.get("RESULTS_BUCKET", "paperpilot-artifacts-local"),
    }


@pytest.fixture(scope="module")
def dynamodb_client(localstack_config):
    """Create DynamoDB client for LocalStack."""
    return boto3.client(
        "dynamodb",
        endpoint_url=localstack_config["endpoint_url"],
        region_name=localstack_config["region"],
        config=Config(retries={"max_attempts": 3}),
    )


@pytest.fixture(scope="module")
def dynamodb_resource(localstack_config):
    """Create DynamoDB resource for LocalStack."""
    return boto3.resource(
        "dynamodb",
        endpoint_url=localstack_config["endpoint_url"],
        region_name=localstack_config["region"],
    )


@pytest.fixture(scope="module")
def sqs_client(localstack_config):
    """Create SQS client for LocalStack."""
    return boto3.client(
        "sqs",
        endpoint_url=localstack_config["endpoint_url"],
        region_name=localstack_config["region"],
    )


@pytest.fixture(scope="module")
def s3_client(localstack_config):
    """Create S3 client for LocalStack."""
    return boto3.client(
        "s3",
        endpoint_url=localstack_config["endpoint_url"],
        region_name=localstack_config["region"],
    )


class TestLocalStackConnectivity:
    """Verify LocalStack is running and accessible."""

    def test_dynamodb_accessible(self, dynamodb_client, localstack_config):
        """DynamoDB in LocalStack is accessible."""
        response = dynamodb_client.list_tables()
        assert "TableNames" in response

    def test_jobs_table_exists(self, dynamodb_client, localstack_config):
        """Jobs table exists in LocalStack."""
        response = dynamodb_client.list_tables()
        assert localstack_config["table_name"] in response["TableNames"]

    def test_sqs_accessible(self, sqs_client, localstack_config):
        """SQS in LocalStack is accessible."""
        response = sqs_client.list_queues()
        assert "QueueUrls" in response

    def test_jobs_queue_exists(self, sqs_client, localstack_config):
        """Jobs queue exists in LocalStack."""
        response = sqs_client.list_queues()
        queue_urls = response.get("QueueUrls", [])
        assert any("paperpilot-jobs" in url for url in queue_urls)

    def test_s3_accessible(self, s3_client):
        """S3 in LocalStack is accessible."""
        response = s3_client.list_buckets()
        assert "Buckets" in response


class TestDynamoDBOperations:
    """Test DynamoDB operations against LocalStack."""

    def test_put_and_get_job(self, dynamodb_resource, localstack_config):
        """Can put and get a job from DynamoDB."""
        table = dynamodb_resource.Table(localstack_config["table_name"])

        test_job = {
            "job_id": "test-integration-job-1",
            "job_type": "pipeline",
            "status": "queued",
            "query": "integration test query",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # Put item
        table.put_item(Item=test_job)

        # Get item
        response = table.get_item(Key={"job_id": "test-integration-job-1"})

        assert "Item" in response
        assert response["Item"]["job_id"] == "test-integration-job-1"
        assert response["Item"]["status"] == "queued"

        # Cleanup
        table.delete_item(Key={"job_id": "test-integration-job-1"})

    def test_update_job_status(self, dynamodb_resource, localstack_config):
        """Can update job status in DynamoDB."""
        table = dynamodb_resource.Table(localstack_config["table_name"])

        # Create job
        test_job = {
            "job_id": "test-integration-job-2",
            "job_type": "pipeline",
            "status": "queued",
            "query": "test",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        table.put_item(Item=test_job)

        # Update status
        table.update_item(
            Key={"job_id": "test-integration-job-2"},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "running"},
        )

        # Verify update
        response = table.get_item(Key={"job_id": "test-integration-job-2"})
        assert response["Item"]["status"] == "running"

        # Cleanup
        table.delete_item(Key={"job_id": "test-integration-job-2"})


class TestSQSOperations:
    """Test SQS operations against LocalStack."""

    def test_send_and_receive_message(self, sqs_client, localstack_config):
        """Can send and receive messages from SQS."""
        queue_url = localstack_config["queue_url"]

        # Send message
        message_body = json.dumps({
            "job_id": "test-sqs-job",
            "job_type": "pipeline",
            "payload": {"query": "test"},
        })

        send_response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
        )
        assert "MessageId" in send_response

        # Receive message
        receive_response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5,
        )

        assert "Messages" in receive_response
        assert len(receive_response["Messages"]) > 0

        message = receive_response["Messages"][0]
        body = json.loads(message["Body"])
        assert body["job_id"] == "test-sqs-job"

        # Delete message
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )


class TestS3Operations:
    """Test S3 operations against LocalStack."""

    def test_put_and_get_object(self, s3_client, localstack_config):
        """Can put and get objects from S3."""
        bucket = localstack_config["bucket_name"]

        # Put object
        test_content = json.dumps({"test": "data"})
        s3_client.put_object(
            Bucket=bucket,
            Key="test/integration-test.json",
            Body=test_content,
            ContentType="application/json",
        )

        # Get object
        response = s3_client.get_object(
            Bucket=bucket,
            Key="test/integration-test.json",
        )

        body = response["Body"].read().decode("utf-8")
        assert json.loads(body) == {"test": "data"}

        # Cleanup
        s3_client.delete_object(
            Bucket=bucket,
            Key="test/integration-test.json",
        )


class TestEndToEndJobFlow:
    """End-to-end test of job creation through completion."""

    def test_job_lifecycle(self, dynamodb_resource, sqs_client, localstack_config):
        """Test the full job lifecycle: create -> queue -> (simulated) process."""
        table = dynamodb_resource.Table(localstack_config["table_name"])
        queue_url = localstack_config["queue_url"]

        job_id = f"e2e-test-{int(time.time())}"

        # 1. Create job in DynamoDB
        job = {
            "job_id": job_id,
            "job_type": "pipeline",
            "status": "queued",
            "query": "end-to-end test",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "progress": {"step": 0, "message": "Waiting..."},
        }
        table.put_item(Item=job)

        # 2. Send job to SQS
        message = json.dumps({
            "job_id": job_id,
            "job_type": "pipeline",
            "payload": {"query": "test", "num_results": 1},
        })
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=message)

        # 3. Verify job is in DynamoDB
        response = table.get_item(Key={"job_id": job_id})
        assert response["Item"]["status"] == "queued"

        # 4. Simulate worker updating status
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, progress = :progress",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "running",
                ":progress": {"step": 1, "message": "Processing..."},
            },
        )

        # 5. Verify running status
        response = table.get_item(Key={"job_id": job_id})
        assert response["Item"]["status"] == "running"

        # 6. Simulate completion
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, #result = :result",
            ExpressionAttributeNames={"#status": "status", "#result": "result"},
            ExpressionAttributeValues={
                ":status": "completed",
                ":result": {"papers_found": 10},
            },
        )

        # 7. Verify completed
        response = table.get_item(Key={"job_id": job_id})
        assert response["Item"]["status"] == "completed"
        assert response["Item"]["result"]["papers_found"] == 10

        # Cleanup
        table.delete_item(Key={"job_id": job_id})

        # Drain any remaining messages
        while True:
            resp = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1,
            )
            if not resp.get("Messages"):
                break
            for msg in resp["Messages"]:
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )
