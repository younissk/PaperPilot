"""AWS Lambda handler for PaperPilot Worker (SQS consumer).

Processes job messages from the SQS queue and updates job state in DynamoDB.

This handler is self-contained to minimize package size.
"""

import json
import os
import logging
from typing import Any
from datetime import datetime, timezone
from enum import Enum

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod")
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)


class JobStatus(str, Enum):
    """Job status values."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def update_job_status(
    job_id: str,
    status: str,
    progress: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Update job status in DynamoDB."""
    update_expr = "SET #status = :status, updated_at = :updated_at"
    expr_names = {"#status": "status"}
    expr_values = {
        ":status": status,
        ":updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if progress is not None:
        update_expr += ", progress = :progress"
        expr_values[":progress"] = progress
    
    if result is not None:
        update_expr += ", #result = :result"
        expr_names["#result"] = "result"
        expr_values[":result"] = result
    
    if error is not None:
        update_expr += ", error_message = :error"
        expr_values[":error"] = error
    
    try:
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        logger.info(f"Updated job {job_id} status to {status}")
    except ClientError as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        raise


def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Process a job based on its type.
    
    Args:
        job_id: Unique job identifier
        job_type: Type of job (search, ranking, clustering, etc.)
        payload: Job-specific parameters
        
    Returns:
        Result dictionary
        
    Raises:
        ValueError: If job_type is unknown
    """
    logger.info(f"Processing job {job_id} of type {job_type}")
    
    # Update status to running
    update_job_status(job_id, JobStatus.RUNNING.value, progress={"step": 0, "message": "Starting..."})
    
    # TODO: Wire up actual job processing based on job_type
    # For now, this is a stub that demonstrates the pattern
    # Heavy ML processing will be added later with Lambda Layers or Container Images
    
    if job_type == "search":
        result = {"message": "Search processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "ranking":
        result = {"message": "Ranking processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "clustering":
        result = {"message": "Clustering processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "timeline":
        result = {"message": "Timeline processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "graph":
        result = {"message": "Graph processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "report":
        result = {"message": "Report processing not yet implemented in worker", "status": "stub"}
        
    elif job_type == "pipeline":
        result = {"message": "Pipeline processing not yet implemented in worker", "status": "stub"}
        
    else:
        raise ValueError(f"Unknown job type: {job_type}")
    
    return result


def handler(event: dict, context) -> dict:
    """Lambda handler for SQS events.
    
    Processes messages from the SQS queue and returns batch item failures
    for any messages that couldn't be processed.
    """
    logger.info(f"Received {len(event.get('Records', []))} records")
    
    batch_item_failures = []
    
    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        job_id = None
        
        try:
            # Parse the message body
            body = json.loads(record.get("body", "{}"))
            
            job_id = body.get("job_id")
            job_type = body.get("job_type")
            payload = body.get("payload", {})
            
            if not job_id or not job_type:
                logger.error("Invalid message format: missing job_id or job_type")
                continue
            
            # Process the job
            result = process_job(job_id, job_type, payload)
            
            # Update job as completed
            update_job_status(job_id, JobStatus.COMPLETED.value, result=result)
            
            logger.info(f"Successfully processed job {job_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message {message_id}: {e}")
            continue
            
        except Exception as e:
            logger.exception(f"Failed to process message {message_id}: {e}")
            
            # Try to update job status to failed
            try:
                if job_id:
                    update_job_status(job_id, JobStatus.FAILED.value, error=str(e))
            except Exception:
                pass
            
            # Add to batch failures for retry
            batch_item_failures.append({"itemIdentifier": message_id})
    
    return {"batchItemFailures": batch_item_failures}
