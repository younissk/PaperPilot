"""Blob Storage helpers for results access."""

from __future__ import annotations

import json
from typing import Any

from .clients import get_results_container_client
from .config import RESULTS_ACCOUNT_URL, RESULTS_CONNECTION_STRING, RESULTS_PREFIX, logger


def results_path(*parts: str) -> str:
    prefix = f"{RESULTS_PREFIX}/" if RESULTS_PREFIX else ""
    return prefix + "/".join(part.strip("/") for part in parts if part)


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

    try:
        container = get_results_container_client()
        blob_client = container.get_blob_client(blob_name)
        content = blob_client.download_blob().readall().decode("utf-8")
        return json.loads(content)
    except ResourceNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in blob %s: %s", blob_name, exc)
        return None
    except Exception as exc:
        logger.error("Failed to read blob %s: %s", blob_name, exc)
        return None


def find_latest_job_for_query(query_slug: str) -> str | None:
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return None

    try:
        container = get_results_container_client()
        prefix = results_path(query_slug)
        job_ids: set[str] = set()

        for blob in container.list_blobs(name_starts_with=f"{prefix}/"):
            parts = blob.name.split("/")
            if len(parts) >= 3:
                job_ids.add(parts[2])

        if not job_ids:
            return None

        return sorted(job_ids)[-1]
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

    metadata = get_query_metadata(query_slug) or {}

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
