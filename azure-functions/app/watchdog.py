"""Timer-triggered watchdog for stale jobs."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import azure.functions as func

from .clients import get_jobs_container
from .config import logger
from .jobs import append_event, update_job_progress
from .utils import is_job_stale

bp = func.Blueprint()


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


@bp.timer_trigger(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def stale_job_watchdog(timer: func.TimerRequest) -> None:
    """Fail jobs that have stopped updating for too long."""
    max_stale_minutes = int(os.getenv("JOB_STALE_MINUTES", "30"))

    try:
        container = get_jobs_container()
    except Exception as exc:
        logger.error("watchdog_failed_to_get_container: %s", exc)
        return

    try:
        items = list(
            container.query_items(
                query="SELECT * FROM c WHERE c.status = @status",
                parameters=[{"name": "@status", "value": "running"}],
                enable_cross_partition_query=True,
            )
        )
    except Exception as exc:
        logger.error("watchdog_query_failed: %s", exc)
        return

    now = datetime.now(UTC)

    for job in items:
        if not is_job_stale(job, max_running_minutes=max_stale_minutes):
            continue

        job_id = job.get("job_id") or job.get("id")
        if not job_id:
            continue

        updated_at = _parse_iso(job.get("updated_at"))
        minutes = None
        if updated_at:
            minutes = int((now - updated_at).total_seconds() // 60)

        message = (
            "Job marked failed by watchdog: no progress updates "
            f"for {minutes or max_stale_minutes} minutes."
        )

        events = job.get("events", []) or []
        events = append_event(
            events,
            "job_failed",
            "error",
            message,
            reason="stale",
            stale_minutes=minutes,
        )
        update_job_progress(
            job_id,
            "failed",
            "error",
            0,
            message,
            events=events,
            error=message,
        )
