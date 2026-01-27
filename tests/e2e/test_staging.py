"""End-to-end tests against the AWS staging environment.

These tests require:
1. A deployed staging stack (Environment=staging)
2. STAGING_API_URL environment variable set to the API Gateway URL

Run with:
    STAGING_API_URL=https://xxx.execute-api.eu-central-1.amazonaws.com pytest tests/e2e/ -v -m e2e
"""

import pytest
import os
import time
import httpx
import boto3

# Mark all tests in this module as e2e tests
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("STAGING_API_URL"),
        reason="STAGING_API_URL not set (staging environment not configured)"
    ),
]


@pytest.fixture(scope="module")
def staging_api_url():
    """Get the staging API URL from environment."""
    url = os.environ.get("STAGING_API_URL", "").rstrip("/")
    return url


@pytest.fixture(scope="module")
def http_client():
    """Create httpx client for API calls."""
    return httpx.Client(timeout=60.0)


@pytest.fixture(scope="module")
def dynamodb_client():
    """Create DynamoDB client for staging verification."""
    return boto3.client(
        "dynamodb",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"),
    )


class TestStagingHealth:
    """Health check tests against staging."""

    def test_health_endpoint_returns_ok(self, staging_api_url, http_client):
        """Staging /api/health returns 200 with ok status."""
        response = http_client.get(f"{staging_api_url}/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_endpoint_returns_info(self, staging_api_url, http_client):
        """Staging / returns API info."""
        response = http_client.get(f"{staging_api_url}/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PaperPilot" in data["message"]


class TestStagingJobCreation:
    """Job creation tests against staging."""

    def test_create_pipeline_job(self, staging_api_url, http_client):
        """Can create a pipeline job in staging."""
        response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "query": "E2E test query - please ignore",
                "num_results": 1,  # Minimal for cost
                "max_iterations": 1,
                "max_accepted": 10,
                "top_n": 5,
                "report_top_k": 3,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

        # Store job_id for later verification
        return data["job_id"]

    def test_get_job_status(self, staging_api_url, http_client):
        """Can get job status from staging."""
        # First create a job
        create_response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "query": "E2E status check test",
                "num_results": 1,
                "max_iterations": 1,
            },
        )
        job_id = create_response.json()["job_id"]

        # Get status
        status_response = http_client.get(f"{staging_api_url}/api/jobs/{job_id}")

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
        assert data["status"] in ["queued", "running", "completed", "failed"]

    def test_nonexistent_job_returns_404(self, staging_api_url, http_client):
        """Getting non-existent job returns 404."""
        response = http_client.get(f"{staging_api_url}/api/jobs/nonexistent-job-id")

        assert response.status_code == 404


class TestStagingJobExecution:
    """Job execution tests against staging (longer running)."""

    @pytest.mark.slow
    def test_job_completes_successfully(self, staging_api_url, http_client):
        """Job eventually completes or fails (doesn't hang).

        This test uses minimal parameters to keep cost/time low.
        """
        # Create job with minimal settings
        create_response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "query": "E2E completion test - small",
                "num_results": 1,
                "max_iterations": 1,
                "max_accepted": 5,
                "top_n": 3,
                "report_top_k": 2,
            },
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["job_id"]

        # Poll for completion (max 5 minutes for tiny job)
        max_wait = 300  # 5 minutes
        poll_interval = 10  # seconds
        elapsed = 0

        while elapsed < max_wait:
            status_response = http_client.get(f"{staging_api_url}/api/jobs/{job_id}")
            assert status_response.status_code == 200

            data = status_response.json()
            status = data["status"]

            if status in ["completed", "failed"]:
                break

            time.sleep(poll_interval)
            elapsed += poll_interval

        # Job should have reached terminal state
        assert status in ["completed", "failed"], f"Job stuck in {status} after {elapsed}s"

        # If completed, verify result structure
        if status == "completed":
            assert "result" in data
            # Result should have expected fields
            result = data.get("result", {})
            # Check for basic result fields (they may vary)
            assert isinstance(result, dict)


class TestStagingValidation:
    """Input validation tests against staging."""

    def test_invalid_query_rejected(self, staging_api_url, http_client):
        """Empty query is rejected."""
        response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "num_results": 5,
                # Missing required 'query' field
            },
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_num_results_rejected(self, staging_api_url, http_client):
        """Invalid num_results is rejected."""
        response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "query": "test",
                "num_results": 0,  # Must be >= 1
            },
        )

        assert response.status_code == 422


class TestStagingDynamoDBIntegration:
    """Verify DynamoDB integration in staging."""

    def test_job_appears_in_dynamodb(self, staging_api_url, http_client, dynamodb_client):
        """Created job appears in staging DynamoDB table."""
        # Create job
        create_response = http_client.post(
            f"{staging_api_url}/api/pipeline",
            json={
                "query": "DynamoDB integration test",
                "num_results": 1,
                "max_iterations": 1,
            },
        )
        job_id = create_response.json()["job_id"]

        # Query DynamoDB directly
        response = dynamodb_client.get_item(
            TableName="paperpilot-jobs-staging",
            Key={"job_id": {"S": job_id}},
        )

        assert "Item" in response
        item = response["Item"]
        assert item["job_id"]["S"] == job_id
        assert item["job_type"]["S"] == "pipeline"
