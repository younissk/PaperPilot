"""Shared pytest fixtures and configuration for PaperPilot tests."""

import os
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

# Ensure test environment variables
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")


# =============================================================================
# Markers registration
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: fast unit tests with no external dependencies")
    config.addinivalue_line("markers", "component: component tests with mocked AWS")
    config.addinivalue_line("markers", "integration: integration tests requiring LocalStack or real AWS")
    config.addinivalue_line("markers", "e2e: end-to-end tests against staging AWS")
    config.addinivalue_line("markers", "smoke: post-deploy smoke tests")


# =============================================================================
# Sample data fixtures
# =============================================================================

@pytest.fixture
def sample_paper_data():
    """Sample paper data for testing."""
    return {
        "paper_id": "W123456789",
        "title": "Large Language Models for Recommendation Systems",
        "abstract": "This paper explores the use of LLMs in recommender systems...",
        "year": 2024,
        "citation_count": 150,
    }


@pytest.fixture
def sample_job_payload():
    """Sample pipeline job payload."""
    return {
        "query": "LLM based recommender systems",
        "num_results": 5,
        "max_iterations": 3,
        "max_accepted": 50,
        "top_n": 20,
        "k_factor": 32.0,
        "pairing": "swiss",
        "early_stop": True,
        "elo_concurrency": 5,
        "report_top_k": 10,
    }


@pytest.fixture
def sample_sqs_record():
    """Sample SQS record as received by Lambda."""
    return {
        "messageId": "msg-123456",
        "receiptHandle": "receipt-handle-abc",
        "body": '{"job_id": "job-123", "job_type": "pipeline", "payload": {"query": "test"}}',
        "attributes": {},
        "messageAttributes": {},
        "md5OfBody": "abc123",
        "eventSource": "aws:sqs",
        "eventSourceARN": "arn:aws:sqs:eu-central-1:123456789012:test-queue",
        "awsRegion": "eu-central-1",
    }


@pytest.fixture
def sample_dynamodb_job():
    """Sample DynamoDB job item with Decimals."""
    return {
        "job_id": "job-123",
        "job_type": "pipeline",
        "status": "running",
        "query": "test query",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:01:00+00:00",
        "progress": {
            "step": Decimal("2"),
            "message": "Processing...",
            "current": Decimal("10"),
            "total": Decimal("50"),
        },
        "payload": {
            "k_factor": Decimal("32"),
            "num_results": Decimal("5"),
        },
    }


# =============================================================================
# Mock fixtures for AWS services
# =============================================================================

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table."""
    table = MagicMock()
    table.put_item = MagicMock(return_value={})
    table.get_item = MagicMock(return_value={"Item": {}})
    table.update_item = MagicMock(return_value={})
    return table


@pytest.fixture
def mock_sqs_client():
    """Mock SQS client."""
    client = MagicMock()
    client.send_message = MagicMock(return_value={"MessageId": "msg-123"})
    client.receive_message = MagicMock(return_value={"Messages": []})
    client.delete_message = MagicMock(return_value={})
    return client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    client = MagicMock()
    client.upload_file = MagicMock(return_value=None)
    client.put_object = MagicMock(return_value={})
    client.get_object = MagicMock(return_value={"Body": MagicMock()})
    return client


# =============================================================================
# Environment fixtures
# =============================================================================

@pytest.fixture
def staging_env():
    """Environment variables for staging tests."""
    return {
        "STAGING_API_URL": os.environ.get("STAGING_API_URL", ""),
        "AWS_DEFAULT_REGION": "eu-central-1",
    }


@pytest.fixture
def prod_env():
    """Environment variables for prod smoke tests."""
    return {
        "PROD_API_URL": os.environ.get("PROD_API_URL", ""),
        "AWS_DEFAULT_REGION": "eu-central-1",
    }


@pytest.fixture
def localstack_env():
    """Environment variables for LocalStack tests."""
    return {
        "AWS_ENDPOINT_URL": "http://localhost:4566",
        "AWS_DEFAULT_REGION": "eu-central-1",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "JOBS_TABLE_NAME": "paperpilot-jobs-prod",
        "SQS_QUEUE_URL": "http://localhost:4566/000000000000/paperpilot-jobs-prod",
        "RESULTS_BUCKET": "paperpilot-artifacts-local",
    }
