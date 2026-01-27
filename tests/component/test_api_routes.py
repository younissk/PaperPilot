"""Component tests for API Lambda routes using FastAPI TestClient and mocked AWS."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Mark all tests in this module as component tests
pytestmark = pytest.mark.component


@pytest.fixture
def mock_aws_services():
    """Mock all AWS services used by the API handler."""
    with patch("services.api.handler.dynamodb") as mock_dynamodb, \
         patch("services.api.handler.sqs") as mock_sqs, \
         patch("services.api.handler.jobs_table") as mock_table:

        # Setup mock table
        mock_table.put_item = MagicMock(return_value={})
        mock_table.get_item = MagicMock(return_value={"Item": None})
        mock_table.update_item = MagicMock(return_value={})

        # Setup mock SQS
        mock_sqs.send_message = MagicMock(return_value={"MessageId": "msg-123"})

        yield {
            "dynamodb": mock_dynamodb,
            "sqs": mock_sqs,
            "table": mock_table,
        }


@pytest.fixture
def api_client(mock_aws_services):
    """Create TestClient with mocked AWS."""
    from fastapi.testclient import TestClient
    from services.api.handler import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_returns_ok(self, api_client):
        """Health endpoint returns 200 with ok status."""
        response = api_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestRootEndpoint:
    """Tests for / root endpoint."""

    def test_root_returns_info(self, api_client):
        """Root endpoint returns API info."""
        response = api_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "PaperPilot API (Serverless)"
        assert data["version"] == "0.1.0"
        assert "endpoints" in data


class TestPipelineEndpoint:
    """Tests for POST /api/pipeline endpoint."""

    def test_create_pipeline_job_success(self, api_client, mock_aws_services):
        """Creating a pipeline job returns 202 with job_id."""
        response = api_client.post(
            "/api/pipeline",
            json={
                "query": "LLM based recommender systems",
                "num_results": 5,
                "max_iterations": 3,
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "message" in data

        # Verify DynamoDB was called
        mock_aws_services["table"].put_item.assert_called_once()

    def test_create_pipeline_job_with_all_params(self, api_client, mock_aws_services):
        """Creating a pipeline job with all parameters works."""
        response = api_client.post(
            "/api/pipeline",
            json={
                "query": "AI in healthcare",
                "num_results": 10,
                "max_iterations": 5,
                "max_accepted": 100,
                "top_n": 30,
                "k_factor": 64.0,
                "pairing": "random",
                "early_stop": False,
                "elo_concurrency": 10,
                "report_top_k": 20,
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"

    def test_create_pipeline_job_invalid_query(self, api_client):
        """Creating a pipeline job without query fails."""
        response = api_client.post(
            "/api/pipeline",
            json={"num_results": 5}
        )

        assert response.status_code == 422  # Validation error

    def test_create_pipeline_job_invalid_num_results(self, api_client):
        """Creating a pipeline job with invalid num_results fails."""
        response = api_client.post(
            "/api/pipeline",
            json={
                "query": "test",
                "num_results": 0,  # Must be >= 1
            }
        )

        assert response.status_code == 422

    def test_pipeline_job_calls_sqs(self, api_client, mock_aws_services):
        """Creating a pipeline job enqueues to SQS."""
        with patch("services.api.handler.SQS_QUEUE_URL", "http://test-queue"):
            response = api_client.post(
                "/api/pipeline",
                json={"query": "test query"}
            )

            assert response.status_code == 202
            mock_aws_services["sqs"].send_message.assert_called_once()


class TestSearchEndpoint:
    """Tests for POST /api/search endpoint."""

    def test_create_search_job_success(self, api_client, mock_aws_services):
        """Creating a search job returns 202 with job_id."""
        response = api_client.post(
            "/api/search",
            json={
                "query": "neural networks",
                "num_results": 10,
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_create_search_job_defaults(self, api_client, mock_aws_services):
        """Search job uses default parameters."""
        response = api_client.post(
            "/api/search",
            json={"query": "test"}
        )

        assert response.status_code == 202


class TestJobStatusEndpoint:
    """Tests for GET /api/jobs/{job_id} endpoint."""

    def test_get_job_not_found(self, api_client, mock_aws_services):
        """Getting non-existent job returns 404."""
        mock_aws_services["table"].get_item.return_value = {"Item": None}

        response = api_client.get("/api/jobs/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_success(self, api_client, mock_aws_services):
        """Getting existing job returns job data."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "job-123",
                "job_type": "pipeline",
                "status": "running",
                "query": "test query",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {
                    "step": Decimal("2"),
                    "message": "Processing...",
                },
            }
        }

        response = api_client.get("/api/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "running"
        assert data["progress"]["step"] == 2  # Decimal converted to int

    def test_get_completed_job_with_result(self, api_client, mock_aws_services):
        """Getting completed job includes result."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "job-456",
                "job_type": "pipeline",
                "status": "completed",
                "query": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z",
                "progress": {"step": Decimal("6"), "message": "Done"},
                "result": {
                    "papers_found": Decimal("50"),
                    "papers_ranked": Decimal("50"),
                    "artifacts": ["results/test/metadata.json"],
                },
            }
        }

        response = api_client.get("/api/jobs/job-456")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["papers_found"] == 50

    def test_get_failed_job_with_error(self, api_client, mock_aws_services):
        """Getting failed job includes error message."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "job-789",
                "job_type": "pipeline",
                "status": "failed",
                "query": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:02:00Z",
                "progress": {"step": Decimal("1"), "message": "Failed"},
                "error_message": "OpenAI API rate limit exceeded",
            }
        }

        response = api_client.get("/api/jobs/job-789")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "rate limit" in data["error_message"].lower()


class TestDecimalConversion:
    """Tests for Decimal conversion in API responses."""

    def test_decimal_integers_become_int(self, api_client, mock_aws_services):
        """Decimal whole numbers become Python ints."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "job-123",
                "job_type": "pipeline",
                "status": "running",
                "query": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {
                    "step": Decimal("5"),
                    "current": Decimal("10"),
                    "total": Decimal("50"),
                },
            }
        }

        response = api_client.get("/api/jobs/job-123")
        data = response.json()

        # These should be ints, not floats
        assert data["progress"]["step"] == 5
        assert isinstance(data["progress"]["step"], int)

    def test_decimal_floats_become_float(self, api_client, mock_aws_services):
        """Decimal fractional numbers become Python floats."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "job-123",
                "job_type": "pipeline",
                "status": "completed",
                "query": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {"step": Decimal("6"), "message": "Done"},
                "result": {
                    "top_papers": [
                        {"elo": Decimal("1650.5"), "title": "Test"},
                    ],
                },
            }
        }

        response = api_client.get("/api/jobs/job-123")
        data = response.json()

        elo = data["result"]["top_papers"][0]["elo"]
        assert elo == 1650.5
        assert isinstance(elo, float)
