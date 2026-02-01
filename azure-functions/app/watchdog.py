"""Timer-triggered watchdog for stale jobs."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta

import azure.functions as func

from .clients import get_jobs_container
from .config import logger
from .jobs import append_event, enqueue_job, update_job_progress
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


def _max_queued_seconds() -> int:
    """Resolve queued-job rescue threshold in seconds.

    Back-compat: supports JOB_QUEUED_MINUTES (deprecated).
    """
    val = os.getenv("JOB_QUEUED_SECONDS")
    if val:
        try:
            return max(1, int(val))
        except ValueError:
            logger.warning("Invalid JOB_QUEUED_SECONDS=%r; falling back to defaults", val)

    minutes = os.getenv("JOB_QUEUED_MINUTES")
    if minutes:
        try:
            logger.warning("JOB_QUEUED_MINUTES is deprecated; use JOB_QUEUED_SECONDS instead")
            return max(1, int(minutes) * 60)
        except ValueError:
            logger.warning("Invalid JOB_QUEUED_MINUTES=%r; falling back to defaults", minutes)

    # Default: keep this low to hide short Service Bus trigger cold starts.
    return 20


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


def _parse_job_updated_at(job: dict) -> datetime | None:
    updated_at = _parse_iso(job.get("updated_at"))
    if updated_at:
        return updated_at
    return _parse_iso(job.get("created_at"))


@bp.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def running_job_rescue_watchdog(timer: func.TimerRequest) -> None:
    """Re-queue running jobs that stopped emitting progress updates.

    This is a "soft" rescue. It does not fail the job; it marks the current stage as queued
    and re-enqueues a message so the worker can retry idempotently.
    """
    rescue_minutes = int(os.getenv("JOB_RUNNING_RESCUE_MINUTES", "8"))
    # Do not try to rescue jobs that are already considered stale enough to be failed.
    fail_minutes = int(os.getenv("JOB_STALE_MINUTES", "30"))

    try:
        container = get_jobs_container()
    except Exception as exc:
        logger.error("running_rescue_failed_to_get_container: %s", exc)
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
        logger.error("running_rescue_query_failed: %s", exc)
        return

    now = datetime.now(UTC)

    for job in items:
        job_id = job.get("job_id") or job.get("id")
        if not job_id:
            continue

        updated_dt = _parse_job_updated_at(job)
        if not updated_dt:
            continue

        minutes = int((now - updated_dt).total_seconds() // 60)
        if minutes < rescue_minutes:
            continue
        if minutes >= fail_minutes:
            # Let stale_job_watchdog handle failures.
            continue

        progress = job.get("progress") or {}
        phase = (progress.get("phase") or "").lower()
        step_name = (progress.get("step_name") or "").lower()
        message = (progress.get("message") or "").lower()

        # If it already looks queued, queued_job_watchdog will handle rescue.
        if "queued" in step_name or "queued" in message:
            continue

        # Only rescue known pipeline stages.
        if phase not in {"search", "ranking", "report"}:
            continue

        payload = job.get("payload") or {}
        next_payload = dict(payload)
        next_payload["stage"] = phase

        events = job.get("events", []) or []
        events = append_event(
            events,
            "progress",
            phase,
            f"Rescue watchdog queued {phase} stage (no updates for {minutes}m)",
            reason="running_rescue_watchdog",
            stale_minutes=minutes,
        )
        update_job_progress(
            job_id,
            "running",
            phase,
            0,
            f"Queued {phase} stage",
            step_name="Queued",
            events=events,
        )

        try:
            enqueue_job(job_id, "pipeline", next_payload)
        except Exception as exc:
            logger.exception("running_rescue_enqueue_failed for job %s", job_id)
            events = append_event(
                events,
                "phase_warning",
                phase,
                f"Rescue watchdog failed to enqueue {phase}: {exc}",
                level="warning",
                error=str(exc),
            )
            update_job_progress(
                job_id,
                "running",
                phase,
                0,
                f"Rescue enqueue failed: {exc}",
                events=events,
            )

@bp.timer_trigger(
    schedule="*/10 * * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def queued_job_watchdog(timer: func.TimerRequest) -> None:
    """Rescue queued jobs when the Service Bus trigger is not consuming."""
    # Use seconds to avoid the coarse "whole minutes" delay that can make short cold starts
    # feel like multi-minute queue times.
    max_queued_seconds = _max_queued_seconds()

    try:
        container = get_jobs_container()
    except Exception as exc:
        logger.error("queued_watchdog_failed_to_get_container: %s", exc)
        return

    try:
        now = datetime.now(UTC)
        cutoff = (now - timedelta(seconds=max_queued_seconds)).isoformat()
        # Pull only jobs that are queued OR are running but stuck on a "Queued" marker.
        # This avoids starvation by long-running jobs, which can have older updated_at values.
        items = list(
            container.query_items(
                query=(
                    "SELECT TOP 5 * FROM c "
                    "WHERE ("
                    "  c.status = @queued "
                    "  OR ("
                    "    c.status = @running "
                    "    AND IS_DEFINED(c.progress) "
                    "    AND ("
                    "      (IS_DEFINED(c.progress.step_name) AND CONTAINS(LOWER(c.progress.step_name), 'queued')) "
                    "      OR (IS_DEFINED(c.progress.message) AND CONTAINS(LOWER(c.progress.message), 'queued')) "
                    "    )"
                    "  )"
                    ") "
                    "AND IS_DEFINED(c.updated_at) AND c.updated_at <= @cutoff "
                    "ORDER BY c.updated_at ASC"
                ),
                parameters=[
                    {"name": "@queued", "value": "queued"},
                    {"name": "@running", "value": "running"},
                    {"name": "@cutoff", "value": cutoff},
                ],
                enable_cross_partition_query=True,
            )
        )
    except Exception as exc:
        logger.error("queued_watchdog_query_failed: %s", exc)
        return

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

        queued_seconds = int((now - updated_at).total_seconds())
        is_queued_marker = "queued" in step_name or "queued" in message or status == "queued"
        if not is_queued_marker or queued_seconds < max_queued_seconds:
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
            logger.info(
                "queued_watchdog_rescue",
                extra={
                    "custom_dimensions": {
                        "job_id": job_id,
                        "stage": stage,
                        "queued_seconds": queued_seconds,
                        "status": status,
                    }
                },
            )
            events = append_event(
                events,
                "progress",
                stage,
                f"Rescue watchdog running {stage} stage (queued {queued_seconds}s)",
                reason="queued_watchdog",
                queued_seconds=queued_seconds,
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
                if result.get("papers_found", 0) <= 0:
                    message = "Search produced 0 papers; cannot continue to ranking/report."
                    events = append_event(events, "job_failed", "search", message, reason="queued_watchdog")
                    update_job_progress(
                        job_id,
                        "failed",
                        "search",
                        0,
                        message,
                        events=events,
                        result=result,
                        error=message,
                    )
                    return
                # Queue next stage (prefer Service Bus when available).
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
                next_payload = dict(payload)
                next_payload["stage"] = "ranking"
                enqueue_job(job_id, "pipeline", next_payload)
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
                next_payload = dict(payload)
                next_payload["stage"] = "report"
                enqueue_job(job_id, "pipeline", next_payload)
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
