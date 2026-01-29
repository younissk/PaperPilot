"""Service Bus worker for processing jobs."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import azure.functions as func

from .config import QUEUE_NAME, logger
from .jobs import append_event, get_job, update_job_progress
from .pipeline import run_pipeline, run_search_job
from .utils import load_openai_api_key

bp = func.Blueprint()


def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    existing_job = get_job(job_id)
    events: list[dict[str, Any]] = existing_job.get("events", []) if existing_job else []
    events = append_event(events, "job_start", "init", f"Starting {job_type} job")
    update_job_progress(job_id, "running", "init", 0, "Initializing...", events=events)

    load_openai_api_key()

    if job_type == "pipeline":
        result = asyncio.run(run_pipeline(job_id, payload, events))
        return result, events
    if job_type == "search":
        result = asyncio.run(run_search_job(job_id, payload, events))
        return result, events

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

        result, events = process_job(job_id, job_type, job_payload)
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
        raise
