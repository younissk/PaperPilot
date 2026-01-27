"""SQS queue service for serverless job submission.

This module provides a QueueService class that sends job messages to SQS,
which are then consumed by the worker Lambda.

Usage:
    from paperpilot.core.queue_service import QueueService, get_queue_service
    
    queue = get_queue_service()
    
    # Enqueue a search job
    queue.enqueue_job(
        job_id="123",
        job_type="search",
        payload={"query": "machine learning", "num_results": 10}
    )
"""

import json
import os
from typing import Any

import boto3


class QueueService:
    """SQS queue service for job submission.
    
    This class provides methods to send job messages to SQS.
    It's designed to be used by the API Lambda to enqueue work
    for the worker Lambda.
    """

    def __init__(self, queue_url: str | None = None):
        """Initialize the queue service.
        
        Args:
            queue_url: SQS queue URL. If None, uses SQS_QUEUE_URL env var.
        """
        self.queue_url = queue_url or os.environ.get(
            "SQS_QUEUE_URL",
            "https://sqs.eu-central-1.amazonaws.com/120569648365/paperpilot-jobs-prod"
        )

        # Lazy initialization of SQS client
        self._sqs = None

    @property
    def sqs(self):
        """Lazy-load SQS client."""
        if self._sqs is None:
            self._sqs = boto3.client("sqs")
        return self._sqs

    def enqueue_job(
        self,
        job_id: str,
        job_type: str,
        payload: dict[str, Any],
        message_group_id: str | None = None,
        deduplication_id: str | None = None,
    ) -> str:
        """Send a job message to the SQS queue.
        
        Args:
            job_id: Unique job identifier
            job_type: Type of job (search, ranking, clustering, etc.)
            payload: Job-specific parameters
            message_group_id: Optional message group ID (for FIFO queues)
            deduplication_id: Optional deduplication ID (for FIFO queues)
            
        Returns:
            Message ID from SQS
            
        Raises:
            ClientError: If message send fails
        """
        message_body = json.dumps({
            "job_id": job_id,
            "job_type": job_type,
            "payload": payload,
        })

        kwargs = {
            "QueueUrl": self.queue_url,
            "MessageBody": message_body,
        }

        # Add FIFO queue attributes if provided
        if message_group_id:
            kwargs["MessageGroupId"] = message_group_id
        if deduplication_id:
            kwargs["MessageDeduplicationId"] = deduplication_id

        response = self.sqs.send_message(**kwargs)
        return response["MessageId"]

    def enqueue_search_job(
        self,
        job_id: str,
        query: str,
        num_results: int = 5,
        max_iterations: int = 5,
        max_accepted: int = 200,
        top_n: int = 50,
    ) -> str:
        """Convenience method to enqueue a search job.
        
        Args:
            job_id: Unique job identifier
            query: Research query string
            num_results: Number of results per query variant
            max_iterations: Maximum snowball iterations
            max_accepted: Maximum total papers to accept
            top_n: Top N candidates to judge per iteration
            
        Returns:
            Message ID from SQS
        """
        return self.enqueue_job(
            job_id=job_id,
            job_type="search",
            payload={
                "query": query,
                "num_results": num_results,
                "max_iterations": max_iterations,
                "max_accepted": max_accepted,
                "top_n": top_n,
            },
        )

    def enqueue_ranking_job(
        self,
        job_id: str,
        query: str,
        file_path: str | None = None,
        n_matches: int | None = None,
        k_factor: float = 32.0,
        pairing: str = "swiss",
        early_stop: bool = True,
        concurrency: int = 5,
    ) -> str:
        """Convenience method to enqueue a ranking job.
        
        Args:
            job_id: Unique job identifier
            query: Research query string
            file_path: Path to snowball results file
            n_matches: Number of matches to run
            k_factor: K-factor for Elo updates
            pairing: Pairing strategy (swiss or random)
            early_stop: Stop when rankings stabilize
            concurrency: Max concurrent API calls
            
        Returns:
            Message ID from SQS
        """
        return self.enqueue_job(
            job_id=job_id,
            job_type="ranking",
            payload={
                "query": query,
                "file_path": file_path,
                "n_matches": n_matches,
                "k_factor": k_factor,
                "pairing": pairing,
                "early_stop": early_stop,
                "concurrency": concurrency,
            },
        )

    def enqueue_pipeline_job(
        self,
        job_id: str,
        query: str,
        num_results: int = 5,
        max_iterations: int = 5,
        max_accepted: int = 200,
        top_n: int = 50,
        k_factor: float = 32.0,
        pairing: str = "swiss",
        early_stop: bool = True,
        elo_concurrency: int = 5,
        report_top_k: int = 30,
    ) -> str:
        """Convenience method to enqueue a full pipeline job.
        
        Args:
            job_id: Unique job identifier
            query: Research query string
            num_results: Number of results per query variant
            max_iterations: Maximum snowball iterations
            max_accepted: Maximum total papers to accept
            top_n: Top N candidates to judge per iteration
            k_factor: K-factor for Elo updates
            pairing: Pairing strategy (swiss or random)
            early_stop: Stop when rankings stabilize
            elo_concurrency: Max concurrent API calls for ELO
            report_top_k: Number of top papers for report
            
        Returns:
            Message ID from SQS
        """
        return self.enqueue_job(
            job_id=job_id,
            job_type="pipeline",
            payload={
                "query": query,
                "num_results": num_results,
                "max_iterations": max_iterations,
                "max_accepted": max_accepted,
                "top_n": top_n,
                "k_factor": k_factor,
                "pairing": pairing,
                "early_stop": early_stop,
                "elo_concurrency": elo_concurrency,
                "report_top_k": report_top_k,
            },
        )


# Module-level singleton for convenience
_default_queue_service: QueueService | None = None


def get_queue_service() -> QueueService:
    """Get the default queue service singleton.
    
    This creates a single service instance that can be reused
    across Lambda invocations (connection reuse).
    
    Returns:
        QueueService instance
    """
    global _default_queue_service
    if _default_queue_service is None:
        _default_queue_service = QueueService()
    return _default_queue_service
