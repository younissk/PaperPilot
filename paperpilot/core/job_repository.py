"""DynamoDB-backed job repository for serverless deployment.

This module provides a JobRepository class that abstracts job state persistence
to DynamoDB, replacing the in-memory jobs dict used in the local API.

Usage:
    from paperpilot.core.job_repository import JobRepository, JobState
    
    repo = JobRepository()  # Uses JOBS_TABLE_NAME env var
    
    # Create a new job
    job = repo.create_job(
        job_type="search",
        query="machine learning",
        payload={"num_results": 10}
    )
    
    # Update job progress
    repo.update_progress(job.job_id, step=1, message="Searching...")
    
    # Get job state
    job = repo.get_job(job_id)
    
    # Mark job complete
    repo.complete_job(job_id, result={"papers": [...]})
"""

import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Default TTL: 7 days
DEFAULT_TTL_DAYS = 7


class JobStatus(str, Enum):
    """Job status values."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobProgress:
    """Job progress information."""
    step: int = 0
    step_name: str = ""
    current: int = 0
    total: int = 0
    message: str = ""
    phase: str = ""  # For pipeline jobs: search, ranking, report
    current_iteration: int = 0
    total_iterations: int = 0


@dataclass
class JobState:
    """Complete job state."""
    job_id: str
    job_type: str
    status: JobStatus
    query: str
    created_at: str
    updated_at: str
    expires_at: int  # Unix timestamp for DynamoDB TTL

    # Optional fields
    payload: dict[str, Any] = field(default_factory=dict)
    progress: JobProgress = field(default_factory=JobProgress)
    result: dict[str, Any] | None = None
    error_message: str | None = None

    # For search/pipeline jobs
    papers: list[dict] = field(default_factory=list)
    report_data: dict[str, Any] | None = None
    query_profile: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        data = {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "query": self.query,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "payload": self.payload,
            "progress": asdict(self.progress) if isinstance(self.progress, JobProgress) else self.progress,
        }

        # Only include optional fields if they have values
        if self.result is not None:
            data["result"] = self.result
        if self.error_message is not None:
            data["error_message"] = self.error_message
        if self.papers:
            data["papers"] = self.papers
        if self.report_data is not None:
            data["report_data"] = self.report_data
        if self.query_profile is not None:
            data["query_profile"] = self.query_profile

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobState":
        """Create JobState from DynamoDB item."""
        progress_data = data.get("progress", {})
        if isinstance(progress_data, dict):
            progress = JobProgress(**progress_data)
        else:
            progress = JobProgress()

        status = data.get("status", "queued")
        if isinstance(status, str):
            try:
                status = JobStatus(status)
            except ValueError:
                status = JobStatus.QUEUED

        return cls(
            job_id=data["job_id"],
            job_type=data.get("job_type", "unknown"),
            status=status,
            query=data.get("query", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            expires_at=data.get("expires_at", 0),
            payload=data.get("payload", {}),
            progress=progress,
            result=data.get("result"),
            error_message=data.get("error_message"),
            papers=data.get("papers", []),
            report_data=data.get("report_data"),
            query_profile=data.get("query_profile"),
        )


class JobRepository:
    """DynamoDB-backed job state repository.
    
    This class provides methods to create, read, and update job state
    in DynamoDB. It's designed to be used by both the API Lambda
    (to create jobs and check status) and the worker Lambda
    (to update progress and results).
    """

    def __init__(
        self,
        table_name: str | None = None,
        ttl_days: int = DEFAULT_TTL_DAYS,
    ):
        """Initialize the repository.
        
        Args:
            table_name: DynamoDB table name. If None, uses JOBS_TABLE_NAME env var.
            ttl_days: Number of days before jobs expire (default: 7)
        """
        self.table_name = table_name or os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod")
        self.ttl_days = ttl_days

        # Lazy initialization of DynamoDB resource
        self._dynamodb = None
        self._table = None

    @property
    def dynamodb(self):
        """Lazy-load DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource("dynamodb")
        return self._dynamodb

    @property
    def table(self):
        """Lazy-load DynamoDB table."""
        if self._table is None:
            self._table = self.dynamodb.Table(self.table_name)
        return self._table

    def _calculate_ttl(self) -> int:
        """Calculate TTL timestamp (Unix epoch seconds)."""
        return int((datetime.now(UTC) + timedelta(days=self.ttl_days)).timestamp())

    def _now_iso(self) -> str:
        """Get current time as ISO string."""
        return datetime.now(UTC).isoformat()

    def create_job(
        self,
        job_type: str,
        query: str,
        payload: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> JobState:
        """Create a new job.
        
        Args:
            job_type: Type of job (search, ranking, clustering, etc.)
            query: Research query string
            payload: Job-specific parameters
            job_id: Optional job ID (generated if not provided)
            
        Returns:
            Created JobState
        """
        now = self._now_iso()
        job = JobState(
            job_id=job_id or str(uuid.uuid4()),
            job_type=job_type,
            status=JobStatus.QUEUED,
            query=query,
            created_at=now,
            updated_at=now,
            expires_at=self._calculate_ttl(),
            payload=payload or {},
            progress=JobProgress(message="Waiting to start..."),
        )

        self.table.put_item(Item=job.to_dict())
        return job

    def get_job(self, job_id: str) -> JobState | None:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobState if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"job_id": job_id})
            item = response.get("Item")
            if item:
                return JobState.from_dict(item)
            return None
        except ClientError as e:
            # Log error but return None
            print(f"Error getting job {job_id}: {e}")
            return None

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: str | None = None,
    ) -> None:
        """Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Optional error message (for failed jobs)
        """
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_names = {"#status": "status"}
        expr_values = {
            ":status": status.value,
            ":updated_at": self._now_iso(),
        }

        if error_message is not None:
            update_expr += ", error_message = :error"
            expr_values[":error"] = error_message

        self.table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def update_progress(
        self,
        job_id: str,
        step: int | None = None,
        step_name: str | None = None,
        current: int | None = None,
        total: int | None = None,
        message: str | None = None,
        phase: str | None = None,
        current_iteration: int | None = None,
        total_iterations: int | None = None,
    ) -> None:
        """Update job progress.
        
        Args:
            job_id: Job identifier
            step: Current step number
            step_name: Human-readable step name
            current: Current progress value
            total: Total progress value
            message: Progress message
            phase: Pipeline phase (search, ranking, report)
            current_iteration: Current iteration (for snowball)
            total_iterations: Total iterations
        """
        # Build progress update
        progress_updates = {}
        if step is not None:
            progress_updates["step"] = step
        if step_name is not None:
            progress_updates["step_name"] = step_name
        if current is not None:
            progress_updates["current"] = current
        if total is not None:
            progress_updates["total"] = total
        if message is not None:
            progress_updates["message"] = message
        if phase is not None:
            progress_updates["phase"] = phase
        if current_iteration is not None:
            progress_updates["current_iteration"] = current_iteration
        if total_iterations is not None:
            progress_updates["total_iterations"] = total_iterations

        if not progress_updates:
            return

        # Build SET expression for each progress field
        set_parts = ["updated_at = :updated_at", "#status = :status"]
        expr_names = {"#status": "status"}
        expr_values = {
            ":updated_at": self._now_iso(),
            ":status": JobStatus.RUNNING.value,
        }

        for key, value in progress_updates.items():
            set_parts.append(f"progress.{key} = :p_{key}")
            expr_values[f":p_{key}"] = value

        self.table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET " + ", ".join(set_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def update_papers(self, job_id: str, papers: list[dict]) -> None:
        """Update job papers list.
        
        Args:
            job_id: Job identifier
            papers: List of paper dictionaries
        """
        self.table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET papers = :papers, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":papers": papers,
                ":updated_at": self._now_iso(),
            },
        )

    def complete_job(
        self,
        job_id: str,
        result: dict[str, Any] | None = None,
        papers: list[dict] | None = None,
        report_data: dict[str, Any] | None = None,
    ) -> None:
        """Mark job as completed.
        
        Args:
            job_id: Job identifier
            result: Optional result data
            papers: Optional papers list
            report_data: Optional report data
        """
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_names = {"#status": "status"}
        expr_values = {
            ":status": JobStatus.COMPLETED.value,
            ":updated_at": self._now_iso(),
        }

        if result is not None:
            update_expr += ", #result = :result"
            expr_names["#result"] = "result"
            expr_values[":result"] = result

        if papers is not None:
            update_expr += ", papers = :papers"
            expr_values[":papers"] = papers

        if report_data is not None:
            update_expr += ", report_data = :report_data"
            expr_values[":report_data"] = report_data

        self.table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def fail_job(self, job_id: str, error_message: str) -> None:
        """Mark job as failed.
        
        Args:
            job_id: Job identifier
            error_message: Error description
        """
        self.update_status(job_id, JobStatus.FAILED, error_message=error_message)

    def set_query_profile(self, job_id: str, query_profile: dict[str, Any]) -> None:
        """Set query profile for a job.
        
        Args:
            job_id: Job identifier
            query_profile: Query profile dictionary
        """
        self.table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET query_profile = :qp, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":qp": query_profile,
                ":updated_at": self._now_iso(),
            },
        )


# Module-level singleton for convenience
_default_repository: JobRepository | None = None


def get_job_repository() -> JobRepository:
    """Get the default job repository singleton.
    
    This creates a single repository instance that can be reused
    across Lambda invocations (connection reuse).
    
    Returns:
        JobRepository instance
    """
    global _default_repository
    if _default_repository is None:
        _default_repository = JobRepository()
    return _default_repository
