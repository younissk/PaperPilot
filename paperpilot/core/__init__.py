"""PaperPilot Core - Pure business logic without presentation dependencies."""

# Serverless infrastructure helpers (available when boto3 is installed)
try:
    from paperpilot.core.job_repository import (
        JobProgress,
        JobRepository,
        JobState,
        JobStatus,
        get_job_repository,
    )
    from paperpilot.core.queue_service import (
        QueueService,
        get_queue_service,
    )
except ImportError:
    # boto3 not available (e.g., local dev without AWS SDK)
    pass
