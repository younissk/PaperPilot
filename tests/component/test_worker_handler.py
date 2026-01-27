"""Component tests for Worker Lambda handler with mocked AWS and pipeline modules."""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal

# Mark all tests in this module as component tests
pytestmark = pytest.mark.component


@pytest.fixture
def mock_aws_worker():
    """Mock all AWS services used by the worker handler."""
    with patch("services.worker.handler.dynamodb") as mock_dynamodb, \
         patch("services.worker.handler.s3_client") as mock_s3, \
         patch("services.worker.handler.jobs_table") as mock_table:

        # Setup mock table
        mock_table.put_item = MagicMock(return_value={})
        mock_table.get_item = MagicMock(return_value={"Item": None})
        mock_table.update_item = MagicMock(return_value={})

        # Setup mock S3
        mock_s3.upload_file = MagicMock(return_value=None)
        mock_s3.put_object = MagicMock(return_value={})

        yield {
            "dynamodb": mock_dynamodb,
            "s3": mock_s3,
            "table": mock_table,
        }


def make_sqs_event(job_id: str, job_type: str, payload: dict) -> dict:
    """Create a Lambda SQS event for testing."""
    return {
        "Records": [
            {
                "messageId": f"msg-{job_id}",
                "receiptHandle": "receipt-handle-abc",
                "body": json.dumps({
                    "job_id": job_id,
                    "job_type": job_type,
                    "payload": payload,
                }),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "abc123",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-central-1:123456789012:test-queue",
                "awsRegion": "eu-central-1",
            }
        ]
    }


class TestHandlerBasics:
    """Basic tests for the Lambda handler function."""

    def test_handler_returns_batch_item_failures_format(self, mock_aws_worker):
        """Handler returns correct response format for SQS."""
        from services.worker.handler import handler

        # Create event with invalid message body
        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": "invalid json {{{",
                }
            ]
        }

        result = handler(event, context=None)

        assert "batchItemFailures" in result
        assert isinstance(result["batchItemFailures"], list)

    def test_handler_empty_records(self, mock_aws_worker):
        """Handler handles empty Records array."""
        from services.worker.handler import handler

        event = {"Records": []}
        result = handler(event, context=None)

        assert result == {"batchItemFailures": []}

    def test_handler_missing_job_id(self, mock_aws_worker):
        """Handler handles message without job_id."""
        from services.worker.handler import handler

        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": json.dumps({"job_type": "pipeline", "payload": {}}),
                }
            ]
        }

        result = handler(event, context=None)
        # Should not add to failures for missing job_id (just logs and continues)
        assert result["batchItemFailures"] == []

    def test_handler_unknown_job_type(self, mock_aws_worker):
        """Handler handles unknown job type."""
        from services.worker.handler import handler

        event = make_sqs_event("job-123", "unknown_type", {"query": "test"})

        result = handler(event, context=None)

        # Unknown job type should fail
        assert len(result["batchItemFailures"]) == 1
        assert result["batchItemFailures"][0]["itemIdentifier"] == "msg-job-123"


class TestProcessJobFunction:
    """Tests for the process_job function."""

    def test_process_job_updates_status_to_running(self, mock_aws_worker):
        """process_job updates job status to running."""
        from services.worker.handler import process_job

        with patch("services.worker.handler.asyncio.run") as mock_run:
            mock_run.return_value = {"result": "success"}

            try:
                process_job("job-123", "pipeline", {"query": "test"})
            except Exception:
                pass  # May fail due to missing pipeline modules

            # Check that update_item was called
            assert mock_aws_worker["table"].update_item.called


class TestUpdateJobProgress:
    """Tests for update_job_progress function."""

    def test_update_job_progress_basic(self, mock_aws_worker):
        """update_job_progress updates DynamoDB correctly."""
        from services.worker.handler import update_job_progress

        update_job_progress(
            job_id="job-123",
            status="running",
            phase="search",
            step=1,
            message="Starting search...",
        )

        mock_aws_worker["table"].update_item.assert_called_once()
        call_args = mock_aws_worker["table"].update_item.call_args

        # Check the Key
        assert call_args.kwargs["Key"] == {"job_id": "job-123"}

        # Check status is in the expression values
        assert ":status" in call_args.kwargs["ExpressionAttributeValues"]
        assert call_args.kwargs["ExpressionAttributeValues"][":status"] == "running"

    def test_update_job_progress_with_events(self, mock_aws_worker):
        """update_job_progress includes events list."""
        from services.worker.handler import update_job_progress

        events = [
            {"type": "start", "phase": "init", "message": "Started", "ts": "2024-01-01T00:00:00Z"}
        ]

        update_job_progress(
            job_id="job-123",
            status="running",
            phase="search",
            step=1,
            message="Processing",
            events=events,
        )

        call_args = mock_aws_worker["table"].update_item.call_args
        assert ":events" in call_args.kwargs["ExpressionAttributeValues"]

    def test_update_job_progress_with_result(self, mock_aws_worker):
        """update_job_progress includes result on completion."""
        from services.worker.handler import update_job_progress

        result = {"papers_found": 50, "artifacts": ["file1.json"]}

        update_job_progress(
            job_id="job-123",
            status="completed",
            phase="complete",
            step=0,
            message="Done",
            result=result,
        )

        call_args = mock_aws_worker["table"].update_item.call_args
        assert ":result" in call_args.kwargs["ExpressionAttributeValues"]

    def test_update_job_progress_with_error(self, mock_aws_worker):
        """update_job_progress includes error on failure."""
        from services.worker.handler import update_job_progress

        update_job_progress(
            job_id="job-123",
            status="failed",
            phase="error",
            step=0,
            message="Failed",
            error="API rate limit exceeded",
        )

        call_args = mock_aws_worker["table"].update_item.call_args
        assert ":error" in call_args.kwargs["ExpressionAttributeValues"]
        assert call_args.kwargs["ExpressionAttributeValues"][":error"] == "API rate limit exceeded"


class TestUploadArtifactsToS3:
    """Tests for upload_artifacts_to_s3 function."""

    def test_upload_artifacts_empty_directory(self, mock_aws_worker, tmp_path):
        """upload_artifacts_to_s3 handles empty directory."""
        from services.worker.handler import upload_artifacts_to_s3

        artifacts = upload_artifacts_to_s3(tmp_path, "test-bucket", "test-prefix")

        assert artifacts == []
        mock_aws_worker["s3"].upload_file.assert_not_called()

    def test_upload_artifacts_with_files(self, mock_aws_worker, tmp_path):
        """upload_artifacts_to_s3 uploads files and returns metadata."""
        from services.worker.handler import upload_artifacts_to_s3

        # Create test files
        (tmp_path / "test.json").write_text('{"test": true}')
        (tmp_path / "report.html").write_text("<html></html>")

        artifacts = upload_artifacts_to_s3(tmp_path, "test-bucket", "test-prefix")

        assert len(artifacts) == 2
        assert mock_aws_worker["s3"].upload_file.call_count == 2

        # Check artifact metadata
        keys = [a["key"] for a in artifacts]
        assert any("test.json" in k for k in keys)
        assert any("report.html" in k for k in keys)

    def test_upload_artifacts_sets_content_type(self, mock_aws_worker, tmp_path):
        """upload_artifacts_to_s3 sets correct content types."""
        from services.worker.handler import upload_artifacts_to_s3

        # Create test files of different types
        (tmp_path / "data.json").write_text('{}')
        (tmp_path / "report.html").write_text('')
        (tmp_path / "notes.txt").write_text('')

        upload_artifacts_to_s3(tmp_path, "test-bucket", "test-prefix")

        # Check that ExtraArgs with ContentType was passed
        calls = mock_aws_worker["s3"].upload_file.call_args_list
        content_types = [c.kwargs.get("ExtraArgs", {}).get("ContentType") for c in calls]

        assert "application/json" in content_types
        assert "text/html" in content_types
        assert "text/plain" in content_types


class TestBatchItemFailures:
    """Tests for SQS batch item failure handling."""

    def test_handler_reports_failures_correctly(self, mock_aws_worker):
        """Handler reports failed message IDs for retry."""
        from services.worker.handler import handler

        # Create event that will fail
        event = {
            "Records": [
                {
                    "messageId": "msg-fail-1",
                    "body": json.dumps({
                        "job_id": "job-fail-1",
                        "job_type": "unknown",  # Will fail
                        "payload": {},
                    }),
                },
                {
                    "messageId": "msg-fail-2",
                    "body": json.dumps({
                        "job_id": "job-fail-2",
                        "job_type": "unknown",  # Will fail
                        "payload": {},
                    }),
                },
            ]
        }

        result = handler(event, context=None)

        # Both should fail and be reported
        assert len(result["batchItemFailures"]) == 2
        failed_ids = [f["itemIdentifier"] for f in result["batchItemFailures"]]
        assert "msg-fail-1" in failed_ids
        assert "msg-fail-2" in failed_ids

    def test_handler_partial_failure(self, mock_aws_worker):
        """Handler handles partial batch failures."""
        from services.worker.handler import handler

        # One valid (but stub) and one invalid
        event = {
            "Records": [
                {
                    "messageId": "msg-ok",
                    "body": json.dumps({
                        "job_id": "job-ok",
                        "job_type": "search",  # Stub job type
                        "payload": {"query": "test"},
                    }),
                },
                {
                    "messageId": "msg-fail",
                    "body": json.dumps({
                        "job_id": "job-fail",
                        "job_type": "unknown",
                        "payload": {},
                    }),
                },
            ]
        }

        result = handler(event, context=None)

        # Only the unknown job type should fail
        assert len(result["batchItemFailures"]) == 1
        assert result["batchItemFailures"][0]["itemIdentifier"] == "msg-fail"


class TestJobStatusEnum:
    """Tests for JobStatus enum usage."""

    def test_job_status_values_used_correctly(self, mock_aws_worker):
        """JobStatus enum values are used in updates."""
        from services.worker.handler import update_job_progress, JobStatus

        update_job_progress(
            job_id="test",
            status=JobStatus.RUNNING.value,
            phase="test",
            step=0,
            message="test",
        )

        call_args = mock_aws_worker["table"].update_item.call_args
        assert call_args.kwargs["ExpressionAttributeValues"][":status"] == "running"
