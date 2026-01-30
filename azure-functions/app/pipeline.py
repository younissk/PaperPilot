"""Pipeline execution and artifact upload helpers."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .clients import get_results_container_client
from .config import RESULTS_CONTAINER, logger
from .jobs import append_event, update_job_progress
from .results import results_path
from .utils import now_iso, slugify


def upload_artifacts_to_blob(local_dir: Path, prefix: str) -> list[dict[str, Any]]:
    from azure.storage.blob import ContentSettings

    container = get_results_container_client()
    artifacts: list[dict[str, Any]] = []

    for file_path in local_dir.rglob("*"):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(local_dir).as_posix()
        blob_name = f"{prefix}/{relative_path}"

        content_type = "application/json"
        if file_path.suffix == ".html":
            content_type = "text/html"
        elif file_path.suffix == ".txt":
            content_type = "text/plain"

        with open(file_path, "rb") as data:
            container.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )

        artifacts.append({
            "name": blob_name,
            "size": file_path.stat().st_size,
            "content_type": content_type,
        })

    return artifacts


async def run_pipeline(job_id: str, payload: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    from papernavigator.elo_ranker import EloRanker, RankerConfig
    from papernavigator.models import SnowballCandidate
    from papernavigator.profiler import generate_query_profile
    from papernavigator.report.generator import generate_report, report_to_dict
    from papernavigator.service import run_search

    query = payload.get("query", "")
    num_results = payload.get("num_results", 5)
    max_iterations = payload.get("max_iterations", 5)
    max_accepted = payload.get("max_accepted", 200)
    top_n = payload.get("top_n", 50)
    k_factor = payload.get("k_factor", 32.0)
    pairing = payload.get("pairing", "swiss")
    early_stop = payload.get("early_stop", True)
    elo_concurrency = payload.get("elo_concurrency", 5)
    report_top_k = payload.get("report_top_k", 30)

    query_slug = slugify(query)

    workspace = Path(tempfile.mkdtemp(prefix=f"papernavigator_{job_id}_"))
    results_dir = workspace / query_slug
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Phase 1: Search
        events = append_event(events, "phase_start", "search", "Starting search phase")
        update_job_progress(job_id, "running", "search", 0, "Starting search...", events=events)

        snowball_path = results_dir / "snowball.json"

        def search_progress_callback(step, step_name, current, total, message, curr_iter, total_iter):
            nonlocal events
            events = append_event(events, "progress", "search", message, step=step, step_name=step_name)
            update_job_progress(
                job_id,
                "running",
                "search",
                step,
                message,
                current=current,
                total=total,
                step_name=step_name,
                events=events,
            )

        accepted_papers = await run_search(
            query=query,
            num_results=num_results,
            output_file=str(snowball_path),
            max_iterations=max_iterations,
            max_accepted=max_accepted,
            top_n=top_n,
            progress_callback=search_progress_callback,
        )

        events = append_event(
            events,
            "phase_complete",
            "search",
            f"Search complete: found {len(accepted_papers)} papers",
        )
        update_job_progress(
            job_id,
            "running",
            "search",
            6,
            f"Search complete: {len(accepted_papers)} papers",
            events=events,
        )

        if not accepted_papers:
            raise ValueError("No papers found during search")

        # Phase 2: Ranking
        events = append_event(events, "phase_start", "ranking", "Starting ELO ranking phase")
        update_job_progress(job_id, "running", "ranking", 0, "Starting ranking...", events=events)

        candidates = [
            SnowballCandidate(
                paper_id=p.paper_id,
                title=p.title,
                abstract=p.abstract,
                year=p.year,
                citation_count=p.citation_count,
                influential_citation_count=0,
                discovered_from=p.discovered_from,
                edge_type=p.edge_type,
                depth=p.depth,
            )
            for p in accepted_papers
        ]

        profile = await generate_query_profile(query)

        ranker_config = RankerConfig(
            k_factor=k_factor,
            pairing_strategy=pairing,
            early_stop_enabled=early_stop,
            batch_size=elo_concurrency,
            interactive=False,
        )

        ranker = EloRanker(profile, candidates, ranker_config)
        ranked_candidates = await ranker.rank_candidates()

        elo_path = results_dir / f"elo_ranked_k{int(k_factor)}_p{pairing}.json"
        elo_data = {
            "query": query,
            "total_ranked": len(ranked_candidates),
            "matches_played": len(ranker.match_history),
            "papers": [
                {
                    "paper_id": c.candidate.paper_id,
                    "title": c.candidate.title,
                    "abstract": (c.candidate.abstract[:500] if c.candidate.abstract else None),
                    "year": c.candidate.year,
                    "citation_count": c.candidate.citation_count,
                    "elo_rating": round(c.elo, 1),
                    "wins": c.wins,
                    "losses": c.losses,
                    "draws": c.draws,
                }
                for c in ranked_candidates
            ],
        }
        with open(elo_path, "w", encoding="utf-8") as f:
            json.dump(elo_data, f, indent=2)

        events = append_event(
            events,
            "phase_complete",
            "ranking",
            f"Ranking complete: {len(ranker.match_history)} matches played",
        )
        update_job_progress(
            job_id,
            "running",
            "ranking",
            1,
            f"Ranking complete: {len(ranker.match_history)} matches",
            events=events,
        )

        # Phase 3: Report
        events = append_event(events, "phase_start", "report", "Starting report generation")
        update_job_progress(job_id, "running", "report", 0, "Starting report...", events=events)

        def report_progress_callback(step, step_name, current, total, message):
            nonlocal events
            events = append_event(events, "progress", "report", message, step=step, step_name=step_name)
            update_job_progress(
                job_id,
                "running",
                "report",
                step,
                message,
                current=current,
                total=total,
                step_name=step_name,
                events=events,
            )

        report = await generate_report(
            snowball_file=snowball_path,
            elo_file=elo_path,
            top_k=report_top_k,
            progress_callback=report_progress_callback,
        )

        report_path = results_dir / f"report_top_k{report_top_k}.json"
        report_dict = report_to_dict(report)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        events = append_event(events, "phase_complete", "report", "Report generation complete")

        # Metadata
        metadata = {
            "snowball_file": "snowball.json",
            "snowball_count": len(accepted_papers),
            "created_at": now_iso(),
            "last_updated": now_iso(),
            "query": query,
            "elo_file": elo_path.name,
            "elo_matches": len(ranker.match_history),
            "elo_papers": len(ranked_candidates),
            "report_file": report_path.name,
            "report_papers_used": report_top_k,
            "report_sections": len(report.current_research),
            "report_generated_at": report.generated_at,
        }
        metadata_path = results_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Upload
        events = append_event(events, "phase_start", "upload", "Uploading artifacts to Blob")
        update_job_progress(job_id, "running", "upload", 0, "Uploading to Blob...", events=events)

        blob_prefix = results_path(query_slug, job_id)
        artifacts = upload_artifacts_to_blob(results_dir, blob_prefix)
        events = append_event(events, "phase_complete", "upload", f"Uploaded {len(artifacts)} files")

        result = {
            "papers_found": len(accepted_papers),
            "papers_ranked": len(ranked_candidates),
            "matches_played": len(ranker.match_history),
            "report_sections": len(report.current_research),
            "results_container": RESULTS_CONTAINER,
            "results_prefix": blob_prefix,
            "artifacts": [a["name"] for a in artifacts],
            "top_papers": [
                {
                    "title": c.candidate.title,
                    "elo": round(c.elo, 1),
                    "paper_id": c.candidate.paper_id,
                }
                for c in ranked_candidates[:5]
            ],
        }

        return result

    finally:
        try:
            shutil.rmtree(workspace)
        except Exception as exc:
            logger.warning("Failed to cleanup workspace %s: %s", workspace, exc)


async def run_search_job(job_id: str, payload: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    from papernavigator.service import run_search

    query = payload.get("query", "")
    num_results = payload.get("num_results", 5)
    max_iterations = payload.get("max_iterations", 5)
    max_accepted = payload.get("max_accepted", 200)
    top_n = payload.get("top_n", 50)

    query_slug = slugify(query)
    workspace = Path(tempfile.mkdtemp(prefix=f"papernavigator_{job_id}_"))
    results_dir = workspace / query_slug
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        events = append_event(events, "phase_start", "search", "Starting search phase")
        update_job_progress(job_id, "running", "search", 0, "Starting search...", events=events)

        snowball_path = results_dir / "snowball.json"

        def search_progress_callback(step, step_name, current, total, message, curr_iter, total_iter):
            nonlocal events
            events = append_event(events, "progress", "search", message, step=step, step_name=step_name)
            update_job_progress(
                job_id,
                "running",
                "search",
                step,
                message,
                current=current,
                total=total,
                step_name=step_name,
                events=events,
            )

        accepted_papers = await run_search(
            query=query,
            num_results=num_results,
            output_file=str(snowball_path),
            max_iterations=max_iterations,
            max_accepted=max_accepted,
            top_n=top_n,
            progress_callback=search_progress_callback,
        )

        events = append_event(
            events,
            "phase_complete",
            "search",
            f"Search complete: found {len(accepted_papers)} papers",
        )
        update_job_progress(
            job_id,
            "running",
            "search",
            6,
            f"Search complete: {len(accepted_papers)} papers",
            events=events,
        )

        metadata = {
            "snowball_file": "snowball.json",
            "snowball_count": len(accepted_papers),
            "created_at": now_iso(),
            "last_updated": now_iso(),
            "query": query,
        }
        metadata_path = results_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        blob_prefix = results_path(query_slug, job_id)
        artifacts = upload_artifacts_to_blob(results_dir, blob_prefix)

        return {
            "papers_found": len(accepted_papers),
            "results_container": RESULTS_CONTAINER,
            "results_prefix": blob_prefix,
            "artifacts": [a["name"] for a in artifacts],
        }

    finally:
        try:
            shutil.rmtree(workspace)
        except Exception as exc:
            logger.warning("Failed to cleanup workspace %s: %s", workspace, exc)
