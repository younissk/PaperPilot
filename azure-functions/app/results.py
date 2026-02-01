"""Blob Storage helpers for results access."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .clients import get_results_container_client
from .config import RESULTS_ACCOUNT_URL, RESULTS_CONNECTION_STRING, RESULTS_PREFIX, logger


def results_path(*parts: str) -> str:
    prefix = f"{RESULTS_PREFIX}/" if RESULTS_PREFIX else ""
    return prefix + "/".join(part.strip("/") for part in parts if part)


def _blob_name_variants(blob_name: str) -> list[str]:
    """Return plausible blob-name variants for prefix drift/migrations.

    This makes reads more resilient when `AZURE_RESULTS_PREFIX` changes over time.
    """
    name = blob_name.strip("/")
    prefix = (RESULTS_PREFIX or "").strip("/")

    variants: list[str] = [name]

    if prefix:
        # If the prefix is duplicated, try removing one layer.
        double_prefix = f"{prefix}/{prefix}/"
        if name.startswith(double_prefix):
            variants.append(name[len(prefix) + 1 :])

        if name.startswith(f"{prefix}/"):
            variants.append(name[len(prefix) + 1 :])
        else:
            variants.append(f"{prefix}/{name}")

    # De-dupe while preserving order
    deduped: list[str] = []
    seen: set[str] = set()
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            deduped.append(v)
    return deduped


def test_storage_connection() -> bool:
    """Test if blob storage is accessible. Returns True if connected, False otherwise."""
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return False

    try:
        container = get_results_container_client()
        # Just check if we can get container properties (lightweight operation)
        container.get_container_properties()
        return True
    except Exception as exc:
        logger.warning("Storage connection test failed: %s", exc)
        return False


def list_result_slugs() -> list[str]:
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        logger.warning("Blob storage not configured; cannot list results")
        return []

    try:
        container = get_results_container_client()
        slugs: set[str] = set()
        prefix = results_path("")

        for blob in container.list_blobs(name_starts_with=prefix):
            parts = blob.name.split("/")
            if len(parts) >= 2:
                slugs.add(parts[1])

        return sorted(slugs)
    except Exception as exc:
        logger.error("Failed to list results from blob storage: %s", exc)
        return []


def get_blob_json(blob_name: str) -> dict[str, Any] | None:
    from azure.core.exceptions import ResourceNotFoundError

    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return None

    container = get_results_container_client()

    for candidate in _blob_name_variants(blob_name):
        try:
            blob_client = container.get_blob_client(candidate)
            content = blob_client.download_blob().readall().decode("utf-8")
            return json.loads(content)
        except ResourceNotFoundError:
            continue
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in blob %s: %s", candidate, exc)
            return None
        except Exception as exc:
            logger.error("Failed to read blob %s: %s", candidate, exc)
            return None

    return None


def download_blob_to_path(blob_name: str, file_path: Path) -> bool:
    from azure.core.exceptions import ResourceNotFoundError

    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return False

    container = get_results_container_client()

    for candidate in _blob_name_variants(blob_name):
        try:
            blob_client = container.get_blob_client(candidate)
            data = blob_client.download_blob().readall()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(data)
            return True
        except ResourceNotFoundError:
            continue
        except Exception as exc:
            logger.error("Failed to download blob %s: %s", candidate, exc)
            return False

    return False


def find_latest_job_for_query(query_slug: str) -> str | None:
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return None

    try:
        container = get_results_container_client()
        prefix = results_path(query_slug)
        job_last_modified: dict[str, datetime] = {}
        job_has_report: set[str] = set()
        job_has_snowball: set[str] = set()

        for blob in container.list_blobs(name_starts_with=f"{prefix}/"):
            if not blob.name.startswith(f"{prefix}/"):
                continue

            suffix = blob.name[len(prefix) + 1 :]
            suffix_parts = suffix.split("/")
            if not suffix_parts:
                continue

            job_id = suffix_parts[0]
            job_last_modified.setdefault(job_id, datetime.min.replace(tzinfo=UTC))
            last_modified = getattr(blob, "last_modified", None)
            if isinstance(last_modified, datetime):
                job_last_modified[job_id] = max(
                    job_last_modified.get(job_id, datetime.min.replace(tzinfo=UTC)),
                    last_modified,
                )

            file_name = suffix_parts[-1]
            if file_name == "snowball.json":
                job_has_snowball.add(job_id)
            elif file_name.startswith("report_top_k") and file_name.endswith(".json"):
                job_has_report.add(job_id)

        if not job_last_modified:
            return None

        # Prefer the latest job that has a report artifact; otherwise fall back to the latest job with snowball data.
        candidates = job_has_report or job_has_snowball or set(job_last_modified)
        return max(candidates, key=lambda jid: job_last_modified.get(jid, datetime.min.replace(tzinfo=UTC)))
    except Exception as exc:
        logger.error("Failed to find jobs for query %s: %s", query_slug, exc)
        return None


def get_query_metadata(query_slug: str) -> dict[str, Any] | None:
    job_id = find_latest_job_for_query(query_slug)
    if not job_id:
        return None

    metadata_blob = results_path(query_slug, job_id, "metadata.json")
    return get_blob_json(metadata_blob)


def get_query_results(query_slug: str) -> dict[str, Any]:
    job_id = find_latest_job_for_query(query_slug)
    result = {
        "report": None,
        "snowball": None,
        "graph": None,
        "timeline": None,
        "clusters": None,
    }

    if not job_id:
        return result

    prefix = results_path(query_slug, job_id)

    metadata = get_blob_json(results_path(query_slug, job_id, "metadata.json")) or {}

    report_file = metadata.get("report_file")
    if report_file:
        result["report"] = get_blob_json(f"{prefix}/{report_file}")

    if not result["report"]:
        result["report"] = get_blob_json(f"{prefix}/report_top_k30.json")
        if not result["report"]:
            for k in [20, 50, 10]:
                result["report"] = get_blob_json(f"{prefix}/report_top_k{k}.json")
                if result["report"]:
                    break

    snowball_file = metadata.get("snowball_file", "snowball.json")
    result["snowball"] = get_blob_json(f"{prefix}/{snowball_file}")

    graph_file = metadata.get("graph_json", "graph.json")
    result["graph"] = get_blob_json(f"{prefix}/{graph_file}")

    timeline_file = metadata.get("timeline_json", "timeline.json")
    result["timeline"] = get_blob_json(f"{prefix}/{timeline_file}")

    clusters_file = metadata.get("clusters_json", "clusters.json")
    result["clusters"] = get_blob_json(f"{prefix}/{clusters_file}")

    return result


def get_all_query_metadata() -> dict[str, dict[str, Any] | None]:
    """Fetch metadata for all query slugs in parallel.

    Returns a dict mapping slug -> metadata (or None if not found).
    This is more efficient than N individual calls due to concurrent execution.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    slugs = list_result_slugs()
    if not slugs:
        return {}

    result: dict[str, dict[str, Any] | None] = {}

    def fetch_metadata(slug: str) -> tuple[str, dict[str, Any] | None]:
        try:
            return slug, get_query_metadata(slug)
        except Exception as exc:
            logger.warning("Failed to fetch metadata for %s: %s", slug, exc)
            return slug, None

    # Use ThreadPoolExecutor for concurrent blob fetches
    # Limit concurrency to avoid overwhelming storage
    max_workers = min(10, len(slugs))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_metadata, slug): slug for slug in slugs}
        for future in as_completed(futures):
            slug, metadata = future.result()
            result[slug] = metadata

    return result


def list_recent_reports(limit: int = 5) -> list[dict[str, Any]]:
    """List the most recently generated reports with summary metadata.

    Returns a list of dicts with keys:
        - query_slug: str
        - query: str
        - generated_at: str (ISO format)
        - total_papers_used: int
        - research_themes: list[str]
    """
    slugs = list_result_slugs()
    if not slugs:
        return []

    reports_with_metadata: list[dict[str, Any]] = []

    for slug in slugs:
        try:
            # Get metadata to check if report exists and get generation time
            metadata = get_query_metadata(slug)
            if not metadata:
                continue

            report_generated_at = metadata.get("report_generated_at")
            if not report_generated_at:
                continue

            # Fetch the report to get query text and research themes
            results = get_query_results(slug)
            report = results.get("report")
            if not report:
                continue

            # Extract research themes from current_research
            current_research = report.get("current_research", [])
            research_themes = [item.get("title", "") for item in current_research[:3]]

            reports_with_metadata.append({
                "query_slug": slug,
                "query": report.get("query", slug),
                "generated_at": report_generated_at,
                "total_papers_used": report.get("total_papers_used", 0),
                "research_themes": research_themes,
            })
        except Exception as exc:
            logger.warning("Failed to get report metadata for %s: %s", slug, exc)
            continue

    # Sort by generated_at descending (most recent first)
    reports_with_metadata.sort(
        key=lambda r: r.get("generated_at", ""),
        reverse=True,
    )

    return reports_with_metadata[:limit]
