"""AWS Lambda handler for PaperPilot Worker (SQS consumer).

Processes job messages from the SQS queue and updates job state in DynamoDB.
"""

import json
import os
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import job repository (uses JOBS_TABLE_NAME env var)
from paperpilot.core.job_repository import get_job_repository, JobStatus


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
        Exception: If processing fails
    """
    logger.info(f"Processing job {job_id} of type {job_type}")
    
    repo = get_job_repository()
    
    # Update status to running
    repo.update_progress(job_id, step=0, message="Starting...")
    
    # TODO: Wire up actual job processing based on job_type
    # For now, this is a stub that demonstrates the pattern
    
    if job_type == "search":
        # from paperpilot.core.service import run_search
        # result = await run_search(...)
        result = {"message": "Search processing not yet implemented in worker"}
        
    elif job_type == "ranking":
        # from paperpilot.core.elo_ranker import EloRanker
        # result = await ranker.rank_candidates(...)
        result = {"message": "Ranking processing not yet implemented in worker"}
        
    elif job_type == "clustering":
        result = {"message": "Clustering processing not yet implemented in worker"}
        
    elif job_type == "timeline":
        result = {"message": "Timeline processing not yet implemented in worker"}
        
    elif job_type == "graph":
        result = {"message": "Graph processing not yet implemented in worker"}
        
    elif job_type == "report":
        result = {"message": "Report processing not yet implemented in worker"}
        
    elif job_type == "pipeline":
        result = {"message": "Pipeline processing not yet implemented in worker"}
        
    else:
        raise ValueError(f"Unknown job type: {job_type}")
    
    return result


def handler(event: dict, context) -> dict:
    """Lambda handler for SQS events.
    
    Processes messages from the SQS queue and returns batch item failures
    for any messages that couldn't be processed.
    
    Args:
        event: SQS event containing Records
        context: Lambda context
        
    Returns:
        Response with batchItemFailures for partial batch response
    """
    logger.info(f"Received {len(event.get('Records', []))} records")
    
    repo = get_job_repository()
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
                logger.error(f"Invalid message format: missing job_id or job_type")
                # Don't retry invalid messages
                continue
            
            # Process the job
            result = process_job(job_id, job_type, payload)
            
            # Update job as completed
            repo.complete_job(job_id, result=result)
            
            logger.info(f"Successfully processed job {job_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message {message_id}: {e}")
            # Don't retry malformed JSON
            continue
            
        except Exception as e:
            logger.exception(f"Failed to process message {message_id}: {e}")
            
            # Try to update job status to failed
            try:
                if job_id:
                    repo.fail_job(job_id, str(e))
            except Exception:
                pass
            
            # Add to batch failures for retry
            batch_item_failures.append({"itemIdentifier": message_id})
    
    return {"batchItemFailures": batch_item_failures}
