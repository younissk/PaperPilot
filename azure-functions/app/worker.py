"""Service Bus worker for processing jobs."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import azure.functions as func

from .config import QUEUE_NAME, logger
from .jobs import append_event, get_job, update_job_progress
from .notifications import send_completion_email, send_failure_email
from .pipeline import run_pipeline, run_search_job
from .utils import is_job_stale, load_openai_api_key

bp = func.Blueprint()


def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    """Process a job and return (result, events, was_processed).
    
    Returns was_processed=False if job was skipped due to idempotency check.
    """
    existing_job = get_job(job_id)
    
    # Idempotency check: skip if job already completed or failed
    if existing_job:
        existing_status = existing_job.get("status")
        if existing_status in ("completed", "failed"):
            logger.info("Job %s already finished with status '%s', skipping re-execution", job_id, existing_status)
            return existing_job.get("result", {}), existing_job.get("events", []), False
        # Check if job is running but stale (stuck)
        if existing_status == "running":
            if is_job_stale(existing_job):
                logger.warning("Job %s is stale (running for too long), allowing retry", job_id)
                # Continue processing - job will be re-run
            else:
                logger.warning("Job %s is already running (possible message redelivery), skipping", job_id)
                return {}, existing_job.get("events", []), False
    
    events: list[dict[str, Any]] = existing_job.get("events", []) if existing_job else []
    events = append_event(events, "job_start", "init", f"Starting {job_type} job")
    update_job_progress(job_id, "running", "init", 0, "Initializing...", events=events)

    load_openai_api_key()

    if job_type == "pipeline":
        result = asyncio.run(run_pipeline(job_id, payload, events))
        return result, events, True
    if job_type == "search":
        result = asyncio.run(run_search_job(job_id, payload, events))
        return result, events, True

    raise ValueError(f"Unknown job type: {job_type}")


@bp.service_bus_queue_trigger(
    arg_name="msg",
    queue_name=QUEUE_NAME,
    connection="AZURE_SERVICE_BUS_CONNECTION_STRING",
)
def process_job_message(msg: func.ServiceBusMessage):
    body = msg.get_body().decode("utf-8")
    logger.info("Processing message: %s", body)

    job_id = None
    try:
        payload = json.loads(body)
        job_id = payload.get("job_id")
        job_type = payload.get("job_type")
        job_payload = payload.get("payload") or {}

        if not job_id or not job_type:
            logger.error("Invalid message: missing job_id or job_type")
            return

        result, events, was_processed = process_job(job_id, job_type, job_payload)
        
        # Only update status if job was actually processed (not skipped due to idempotency)
        if was_processed:
            events = append_event(events, "job_complete", "complete", "Job completed")
            update_job_progress(
                job_id,
                "completed",
                "complete",
                0,
                "Job completed",
                events=events,
                result=result,
            )

            # Send completion email notification if requested
            notification_email = job_payload.get("notification_email")
            if notification_email:
                query = job_payload.get("query", "")
                email_sent = send_completion_email(notification_email, query, job_id, result)
                if email_sent:
                    events = append_event(events, "email_sent", "complete", f"Notification sent to {notification_email}")
                    update_job_progress(job_id, "completed", "complete", 0, "Job completed", events=events, result=result)
        else:
            logger.info("Job %s was skipped (idempotency), not updating status", job_id)

    except Exception as exc:
        logger.exception("Error processing message for job %s: %s", job_id, exc)
        if job_id:
            existing_job = get_job(job_id)
            existing_events = existing_job.get("events", []) if existing_job else []

            events = append_event(
                existing_events,
                "job_failed",
                "error",
                f"Job failed: {exc}",
            )
            update_job_progress(
                job_id,
                "failed",
                "error",
                0,
                f"Job failed: {exc}",
                events=events,
                error=str(exc),
            )

            # Send failure email notification if requested
            notification_email = job_payload.get("notification_email") if job_payload else None
            if notification_email:
                query = job_payload.get("query", "") if job_payload else ""
                send_failure_email(notification_email, query, job_id, str(exc))
        raise
