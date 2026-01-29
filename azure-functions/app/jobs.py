"""Cosmos DB job storage + Service Bus enqueue helpers."""

from __future__ import annotations

import json
import uuid
from typing import Any

from .clients import get_jobs_container, get_service_bus_client
from .config import MAX_EVENTS, QUEUE_NAME, SERVICE_BUS_CONNECTION, logger
from .utils import expires_at, now_iso


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


def create_job(job_type: str, query: str, payload: dict[str, Any]) -> str:
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

    container = get_jobs_container()
    container.create_item(job)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    from azure.cosmos import exceptions as cosmos_exceptions

    container = get_jobs_container()
    try:
        return container.read_item(item=job_id, partition_key=job_id)
    except cosmos_exceptions.CosmosResourceNotFoundError:
        return None


def update_job_document(job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    from azure.cosmos import exceptions as cosmos_exceptions

    container = get_jobs_container()
    try:
        job = container.read_item(item=job_id, partition_key=job_id)
    except cosmos_exceptions.CosmosResourceNotFoundError:
        return None

    job.update(updates)
    container.replace_item(item=job_id, body=job)
    return job


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
