"""Timer-triggered watchdog for stale jobs."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import azure.functions as func

from .clients import get_jobs_container
from .config import logger
from .jobs import append_event, update_job_progress
from .pipeline import run_ranking_stage, run_report_stage, run_search_job
from .utils import is_job_stale, load_openai_api_key

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


@bp.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def queued_job_watchdog(timer: func.TimerRequest) -> None:
    """Rescue queued jobs when the Service Bus trigger is not consuming."""
    max_queued_minutes = int(os.getenv("JOB_QUEUED_MINUTES", "3"))

    try:
        container = get_jobs_container()
    except Exception as exc:
        logger.error("queued_watchdog_failed_to_get_container: %s", exc)
        return

    try:
        items = list(
            container.query_items(
                query="SELECT * FROM c WHERE c.status = @queued OR c.status = @running",
                parameters=[
                    {"name": "@queued", "value": "queued"},
                    {"name": "@running", "value": "running"},
                ],
                enable_cross_partition_query=True,
            )
        )
    except Exception as exc:
        logger.error("queued_watchdog_query_failed: %s", exc)
        return

    now = datetime.now(UTC)

    for job in items:
        job_id = job.get("job_id") or job.get("id")
        if not job_id:
            continue

        progress = job.get("progress") or {}
        status = job.get("status")
        phase = (progress.get("phase") or "init").lower()
        step_name = (progress.get("step_name") or "").lower()
        message = (progress.get("message") or "").lower()

        # Only rescue if job is queued (or stuck on a queued marker) for too long
        updated_at = _parse_iso(job.get("updated_at"))
        if not updated_at:
            updated_at = _parse_iso(job.get("created_at"))
        if not updated_at:
            continue

        minutes = int((now - updated_at).total_seconds() // 60)
        is_queued_marker = "queued" in step_name or "queued" in message or status == "queued"
        if not is_queued_marker or minutes < max_queued_minutes:
            continue

        # Determine stage to run based on phase
        if phase in ("init", ""):
            stage = "search"
        elif phase in ("search", "ranking", "report"):
            stage = phase
        else:
            logger.warning("queued_watchdog_unknown_phase", job_id=job_id, phase=phase)
            continue

        payload = job.get("payload") or {}
        events = job.get("events", []) or []

        try:
            load_openai_api_key()
            events = append_event(
                events,
                "progress",
                stage,
                f"Rescue watchdog running {stage} stage (queued {minutes}m)",
                reason="queued_watchdog",
            )
            update_job_progress(
                job_id,
                "running",
                stage,
                0,
                f"Rescue watchdog running {stage} stage",
                step_name="Rescue",
                events=events,
            )

            if stage == "search":
                result = asyncio.run(run_search_job(job_id, payload, events))
                # Queue next stage in-job (no Service Bus)
                events = append_event(
                    events,
                    "progress",
                    "ranking",
                    "Queued ranking stage",
                    step=0,
                    step_name="Queued",
                    reason="queued_watchdog",
                )
                update_job_progress(
                    job_id,
                    "running",
                    "ranking",
                    0,
                    "Queued ranking stage",
                    step_name="Queued",
                    events=events,
                    result=result,
                )
            elif stage == "ranking":
                result = asyncio.run(run_ranking_stage(job_id, payload, events))
                events = append_event(
                    events,
                    "progress",
                    "report",
                    "Queued report stage",
                    step=0,
                    step_name="Queued",
                    reason="queued_watchdog",
                )
                update_job_progress(
                    job_id,
                    "running",
                    "report",
                    0,
                    "Queued report stage",
                    step_name="Queued",
                    events=events,
                    result=result,
                )
            elif stage == "report":
                result = asyncio.run(run_report_stage(job_id, payload, events))
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
            # Only rescue one job per tick to avoid overruns
            return
        except Exception as exc:
            logger.exception("queued_watchdog_failed for job %s: %s", job_id, exc)
            events = append_event(
                events,
                "job_failed",
                "error",
                f"Rescue watchdog failed: {exc}",
                reason="queued_watchdog",
            )
            update_job_progress(
                job_id,
                "failed",
                "error",
                0,
                f"Rescue watchdog failed: {exc}",
                events=events,
                error=str(exc),
            )
            return
