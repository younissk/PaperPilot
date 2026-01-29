"""Cosmos DB job storage + Service Bus enqueue helpers."""

from __future__ import annotations

import json
import uuid
from typing import Any

from .clients import get_jobs_container, get_service_bus_client
from .config import COSMOS_ENDPOINT, COSMOS_KEY, MAX_EVENTS, QUEUE_NAME, SERVICE_BUS_CONNECTION, logger
from .utils import expires_at, now_iso


def test_cosmos_connection() -> bool:
    """Test if Cosmos DB is accessible. Returns True if connected, False otherwise."""
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        return False

    try:
        container = get_jobs_container()
        # Just check if we can query (lightweight operation)
        list(container.query_items(query="SELECT TOP 1 c.id FROM c", enable_cross_partition_query=True))
        return True
    except Exception as exc:
        logger.warning("Cosmos DB connection test failed: %s", exc)
        return False


def append_event(
    events: list[dict[str, Any]],
    event_type: str,
    phase: str,
    message: str,
    **kwargs,
) -> list[dict[str, Any]]:
    event = {
        "ts": now_iso(),
        "type": event_type,
        "phase": phase,
        "message": message,
        **kwargs,
    }
    events.append(event)
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]
    return events


def create_job(job_type: str, query: str, payload: dict[str, Any]) -> str | None:
    """Create a new job in Cosmos DB. Returns job_id on success, None on failure."""
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        logger.error("Cannot create job: Cosmos DB not configured")
        return None

    job_id = str(uuid.uuid4())
    now = now_iso()

    events: list[dict[str, Any]] = []
    events = append_event(
        events,
        "job_created",
        "init",
        "Job created",
        job_type=job_type,
        query=query,
    )

    job = {
        "id": job_id,
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "query": query,
        "payload": payload,
        "created_at": now,
        "updated_at": now,
        "expires_at": expires_at(),
        "events": events,
        "progress": {
            "phase": "init",
            "step": 0,
            "message": "Waiting to start...",
            "current": 0,
            "total": 0,
        },
    }

    try:
        container = get_jobs_container()
        container.create_item(job)
        return job_id
    except Exception as exc:
        logger.error("Failed to create job in Cosmos DB: %s", exc)
        return None


def get_job(job_id: str) -> dict[str, Any] | None:
    """Retrieve a job from Cosmos DB. Returns None if not found or on error."""
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        logger.warning("Cannot get job: Cosmos DB not configured")
        return None

    try:
        container = get_jobs_container()
        # IMPORTANT: Avoid read_item(id, partition_key=...) because an incorrect partition_key
        # yields a 404 even when the document exists. We query by id/job_id instead.
        items = list(
            container.query_items(
                query="SELECT TOP 1 * FROM c WHERE c.id = @id OR c.job_id = @id",
                parameters=[{"name": "@id", "value": job_id}],
                enable_cross_partition_query=True,
            )
        )
        return items[0] if items else None
    except Exception as exc:
        logger.error("Failed to get job %s from Cosmos DB: %s", job_id, exc)
        return None


def update_job_document(job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a job document in Cosmos DB. Returns updated job or None on failure."""
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        logger.warning("Cannot update job: Cosmos DB not configured")
        return None

    try:
        container = get_jobs_container()
        job = get_job(job_id)
        if not job:
            return None
        job.update(updates)
        # Use upsert to avoid needing to know the container's partition key value here.
        container.upsert_item(job)
        return job
    except Exception as exc:
        logger.error("Failed to update job %s in Cosmos DB: %s", job_id, exc)
        return None


def append_job_event(
    job_id: str,
    event_type: str,
    phase: str,
    message: str,
    **kwargs,
) -> None:
    job = get_job(job_id)
    if not job:
        return

    events = job.get("events", []) or []
    events = append_event(events, event_type, phase, message, **kwargs)
    update_job_document(job_id, {"events": events, "updated_at": now_iso()})


def enqueue_job(job_id: str, job_type: str, payload: dict[str, Any]) -> None:
    from azure.servicebus import ServiceBusMessage

    if not SERVICE_BUS_CONNECTION:
        logger.warning("Service Bus connection string not set; skipping enqueue")
        return

    message_body = json.dumps({
        "job_id": job_id,
        "job_type": job_type,
        "payload": payload,
    })

    with get_service_bus_client() as sb_client:
        with sb_client.get_queue_sender(QUEUE_NAME) as sender:
            sender.send_messages(ServiceBusMessage(message_body))

    append_job_event(
        job_id,
        "job_enqueued",
        "init",
        "Job enqueued to Service Bus",
        queue=QUEUE_NAME,
    )


def update_job_progress(
    job_id: str,
    status: str,
    phase: str,
    step: int,
    message: str,
    current: int = 0,
    total: int = 0,
    step_name: str | None = None,
    events: list[dict[str, Any]] | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    updates: dict[str, Any] = {
        "status": status,
        "updated_at": now_iso(),
        "progress": {
            "phase": phase,
            "step": step,
            "step_name": step_name,
            "message": message,
            "current": current,
            "total": total,
        },
    }

    if events is not None:
        updates["events"] = events
    if result is not None:
        updates["result"] = result
    if error is not None:
        updates["error_message"] = error

    updated = update_job_document(job_id, updates)
    if updated is None:
        logger.warning("Job %s not found while updating progress", job_id)
