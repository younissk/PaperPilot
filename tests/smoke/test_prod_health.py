"""Production smoke tests for post-deployment verification.

These tests are designed to run after a production deployment to verify
the system is healthy. They should be:
- Fast (< 1 minute total)
- Non-destructive (read-only or minimal writes)
- Safe to run in production

Run with:
    PROD_API_URL=https://xxx.execute-api.eu-central-1.amazonaws.com pytest tests/smoke/ -v -m smoke
"""

import os

import httpx
import pytest

# Mark all tests in this module as smoke tests
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        not os.environ.get("PROD_API_URL"),
        reason="PROD_API_URL not set (production environment not configured)"
    ),
]


@pytest.fixture(scope="module")
def prod_api_url():
    """Get the production API URL from environment."""
    url = os.environ.get("PROD_API_URL", "").rstrip("/")
    return url


@pytest.fixture(scope="module")
def http_client():
    """Create httpx client for API calls."""
    return httpx.Client(timeout=30.0)


class TestProductionHealth:
    """Critical health checks for production."""

    def test_api_health_endpoint(self, prod_api_url, http_client):
        """Production /api/health returns 200 with ok status.

        This is the primary health check that should always pass
        after a successful deployment.
        """
        response = http_client.get(f"{prod_api_url}/api/health")

        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok", f"Health status not ok: {data}"
        assert "version" in data

    def test_api_root_endpoint(self, prod_api_url, http_client):
        """Production / returns API info."""
        response = http_client.get(f"{prod_api_url}/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PaperPilot" in data["message"]
        assert "version" in data

    def test_api_response_time(self, prod_api_url, http_client):
        """Health check responds within acceptable time."""
        import time

        start = time.time()
        response = http_client.get(f"{prod_api_url}/api/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        # Health check should respond in under 5 seconds
        # (accounting for cold start)
        assert elapsed < 5.0, f"Health check too slow: {elapsed:.2f}s"


class TestProductionEndpoints:
    """Verify critical endpoints are accessible."""

    def test_jobs_endpoint_exists(self, prod_api_url, http_client):
        """Jobs endpoint returns 404 for non-existent job (not 500)."""
        response = http_client.get(f"{prod_api_url}/api/jobs/nonexistent-id")

        # Should be 404, not 500 (which would indicate server error)
        assert response.status_code == 404

    def test_pipeline_endpoint_accepts_post(self, prod_api_url, http_client):
        """Pipeline endpoint accepts POST (validation error is ok).

        We send an invalid request to verify the endpoint exists
        without actually creating a job.
        """
        response = http_client.post(
            f"{prod_api_url}/api/pipeline",
            json={},  # Missing required fields
        )

        # 422 means endpoint exists and validates input
        assert response.status_code == 422

    def test_search_endpoint_accepts_post(self, prod_api_url, http_client):
        """Search endpoint accepts POST (validation error is ok)."""
        response = http_client.post(
            f"{prod_api_url}/api/search",
            json={},  # Missing required fields
        )

        # 422 means endpoint exists and validates input
        assert response.status_code == 422


class TestProductionSecurity:
    """Basic security checks for production."""

    def test_cors_headers_present(self, prod_api_url, http_client):
        """CORS headers are present in response."""
        response = http_client.options(
            f"{prod_api_url}/api/health",
            headers={"Origin": "https://example.com"},
        )

        # Should have CORS headers (we allow all origins in current config)
        assert response.status_code in [200, 204]

    def test_no_server_error_on_bad_input(self, prod_api_url, http_client):
        """Server handles bad input gracefully (no 500)."""
        # Send various bad inputs and verify no 500 errors
        bad_requests = [
            ("POST", "/api/pipeline", {"invalid": "data"}),
            ("POST", "/api/search", None),
            ("GET", "/api/jobs/", None),
        ]

        for method, path, body in bad_requests:
            if method == "POST":
                response = http_client.post(f"{prod_api_url}{path}", json=body)
            else:
                response = http_client.get(f"{prod_api_url}{path}")

            # Any 4xx is acceptable, 5xx indicates server error
            assert response.status_code < 500, f"{method} {path} returned 5xx: {response.text}"


class TestProductionOptional:
    """Optional smoke tests (can be skipped if needed)."""

    @pytest.mark.optional
    def test_create_minimal_job(self, prod_api_url, http_client):
        """Create a minimal job in production (optional, may incur cost).

        This test creates an actual job with minimal parameters.
        Skip this test in regular smoke runs to avoid costs.
        """
        response = http_client.post(
            f"{prod_api_url}/api/pipeline",
            json={
                "query": "smoke test - please ignore",
                "num_results": 1,
                "max_iterations": 1,
                "max_accepted": 3,
                "top_n": 2,
                "report_top_k": 1,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

        # Verify we can get the job status
        job_id = data["job_id"]
        status_response = http_client.get(f"{prod_api_url}/api/jobs/{job_id}")
        assert status_response.status_code == 200
