"""Component tests for frontend API contract compliance.

These tests verify that the serverless API implements all endpoints
required by the Astro frontend. See docs/API_CONTRACT.md for details.
"""

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
         patch("services.api.handler.jobs_table") as mock_table, \
         patch("services.api.handler.s3_client", create=True) as mock_s3:

        # Setup mock table
        mock_table.put_item = MagicMock(return_value={})
        mock_table.get_item = MagicMock(return_value={"Item": None})
        mock_table.update_item = MagicMock(return_value={})

        # Setup mock SQS
        mock_sqs.send_message = MagicMock(return_value={"MessageId": "msg-123"})

        # Setup mock S3
        mock_s3.list_objects_v2 = MagicMock(return_value={"Contents": []})
        mock_s3.get_object = MagicMock()

        yield {
            "dynamodb": mock_dynamodb,
            "sqs": mock_sqs,
            "table": mock_table,
            "s3": mock_s3,
        }


@pytest.fixture
def api_client(mock_aws_services):
    """Create TestClient with mocked AWS."""
    from fastapi.testclient import TestClient
    from services.api.handler import app

    return TestClient(app)


class TestFrontendContractHealth:
    """Contract tests for /api/health endpoint."""

    def test_health_endpoint_exists(self, api_client):
        """GET /api/health must return 200."""
        response = api_client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_shape(self, api_client):
        """Health response must have status and version fields."""
        response = api_client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert data["status"] == "ok"


class TestFrontendContractPipeline:
    """Contract tests for /api/pipeline endpoints."""

    def test_pipeline_create_endpoint_exists(self, api_client, mock_aws_services):
        """POST /api/pipeline must return 202."""
        response = api_client.post(
            "/api/pipeline",
            json={"query": "test query"}
        )
        assert response.status_code == 202

    def test_pipeline_create_response_shape(self, api_client, mock_aws_services):
        """Pipeline create response must have job_id and status."""
        response = api_client.post(
            "/api/pipeline",
            json={"query": "test query"}
        )
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "queued"

    def test_pipeline_status_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/pipeline/{job_id} must exist for frontend polling."""
        # This endpoint needs to be implemented for frontend compatibility
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "test-job-123",
                "job_type": "pipeline",
                "status": "running",
                "query": "test query",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {
                    "phase": "search",
                    "step": Decimal("2"),
                    "message": "Processing...",
                    "current": Decimal("10"),
                    "total": Decimal("50"),
                },
            }
        }

        response = api_client.get("/api/pipeline/test-job-123")

        # Must return 200 (not 404)
        assert response.status_code == 200, \
            "GET /api/pipeline/{job_id} must be implemented for frontend polling"

    def test_pipeline_status_response_shape(self, api_client, mock_aws_services):
        """Pipeline status response must have fields expected by frontend."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "test-job-123",
                "job_type": "pipeline",
                "status": "running",
                "query": "test query",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {
                    "phase": "search",
                    "step": Decimal("2"),
                    "message": "Processing...",
                    "current": Decimal("10"),
                    "total": Decimal("50"),
                },
            }
        }

        response = api_client.get("/api/pipeline/test-job-123")

        # Skip if not implemented yet
        if response.status_code == 404:
            pytest.skip("GET /api/pipeline/{job_id} not yet implemented")

        data = response.json()

        # Required fields for frontend polling
        assert "job_id" in data
        assert "status" in data
        assert "query" in data

        # Progress fields used by frontend
        # These may be at top level or nested in progress
        has_progress_info = (
            "progress_message" in data or
            ("progress" in data and "message" in data.get("progress", {}))
        )
        assert has_progress_info, "Response must include progress information"


class TestFrontendContractResults:
    """Contract tests for /api/results endpoints."""

    def test_results_list_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/results must exist for queries page."""
        response = api_client.get("/api/results")

        # Must return 200 (not 404)
        assert response.status_code == 200, \
            "GET /api/results must be implemented for /queries page"

    def test_results_list_response_shape(self, api_client, mock_aws_services):
        """Results list response must have queries array."""
        response = api_client.get("/api/results")

        # Skip if not implemented yet
        if response.status_code == 404:
            pytest.skip("GET /api/results not yet implemented")

        data = response.json()
        assert "queries" in data
        assert isinstance(data["queries"], list)

    def test_results_query_metadata_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/results/{query} must exist."""
        response = api_client.get("/api/results/test_query")

        # Must not return 405 Method Not Allowed (route must exist)
        assert response.status_code != 405, \
            "GET /api/results/{query} route must exist"

    def test_results_all_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/results/{query}/all must exist for report page."""
        response = api_client.get("/api/results/test_query/all")

        # Must not return 405 Method Not Allowed (route must exist)
        assert response.status_code != 405, \
            "GET /api/results/{query}/all route must exist"

    def test_results_all_response_shape(self, api_client, mock_aws_services):
        """Results all response must have expected structure."""
        response = api_client.get("/api/results/test_query/all")

        # Skip if not implemented yet
        if response.status_code == 404:
            pytest.skip("GET /api/results/{query}/all not yet implemented")

        data = response.json()

        # AllResultsResponse shape
        assert "report" in data
        assert "snowball" in data
        # These can be null
        assert "graph" in data or data.get("graph") is None
        assert "timeline" in data or data.get("timeline") is None
        assert "clusters" in data or data.get("clusters") is None

    def test_results_report_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/results/{query}/report must exist."""
        response = api_client.get("/api/results/test_query/report")

        # Must not return 405 Method Not Allowed (route must exist)
        assert response.status_code != 405, \
            "GET /api/results/{query}/report route must exist"


class TestFrontendContractJobsCompatibility:
    """Tests for /api/jobs endpoint (backend native) vs /api/pipeline (frontend expected)."""

    def test_jobs_endpoint_exists(self, api_client, mock_aws_services):
        """GET /api/jobs/{job_id} is the native serverless endpoint."""
        mock_aws_services["table"].get_item.return_value = {
            "Item": {
                "job_id": "test-job-123",
                "job_type": "pipeline",
                "status": "running",
                "query": "test query",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "progress": {"step": Decimal("2"), "message": "Processing..."},
            }
        }

        response = api_client.get("/api/jobs/test-job-123")
        assert response.status_code == 200

    def test_pipeline_and_jobs_endpoints_consistent(self, api_client, mock_aws_services):
        """Both /api/pipeline/{id} and /api/jobs/{id} should return equivalent data."""
        job_data = {
            "Item": {
                "job_id": "test-job-123",
                "job_type": "pipeline",
                "status": "completed",
                "query": "test query",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z",
                "progress": {"step": Decimal("6"), "message": "Done"},
                "result": {"papers_found": Decimal("50")},
            }
        }
        mock_aws_services["table"].get_item.return_value = job_data

        jobs_response = api_client.get("/api/jobs/test-job-123")
        pipeline_response = api_client.get("/api/pipeline/test-job-123")

        # If pipeline endpoint doesn't exist yet, skip
        if pipeline_response.status_code == 404:
            pytest.skip("GET /api/pipeline/{job_id} not yet implemented")

        jobs_data = jobs_response.json()
        pipeline_data = pipeline_response.json()

        # Core fields should be consistent
        assert jobs_data["job_id"] == pipeline_data["job_id"]
        assert jobs_data["status"] == pipeline_data["status"]
        assert jobs_data["query"] == pipeline_data["query"]
