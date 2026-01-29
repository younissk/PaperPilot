"""PaperPilot Azure Functions API + Worker.

Implements the serverless backend on Azure:
- HTTP API endpoints (health, pipeline/search jobs, results)
- Service Bus worker for pipeline processing
- Cosmos DB for job state
- Azure Blob Storage for results artifacts
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("paperpilot.azure")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COSMOS_ENDPOINT = os.environ.get("AZURE_COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("AZURE_COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("AZURE_COSMOS_DATABASE", "paperpilot")
COSMOS_CONTAINER = os.environ.get("AZURE_COSMOS_CONTAINER", "jobs")

SERVICE_BUS_CONNECTION = os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING", "")
QUEUE_NAME = os.environ.get("AZURE_SERVICE_BUS_QUEUE_NAME", "paperpilot-jobs")

RESULTS_CONNECTION_STRING = (
    os.environ.get("AZURE_RESULTS_CONNECTION_STRING")
    or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    or os.environ.get("AzureWebJobsStorage", "")
)
RESULTS_ACCOUNT_URL = os.environ.get("AZURE_STORAGE_ACCOUNT_URL", "")
RESULTS_CONTAINER = os.environ.get("AZURE_RESULTS_CONTAINER", "results")
RESULTS_PREFIX = os.environ.get("AZURE_RESULTS_PREFIX", "results").strip("/")

OPENAI_API_KEY_SECRET_NAME = os.environ.get("OPENAI_API_KEY_SECRET_NAME", "")
AZURE_KEY_VAULT_URL = os.environ.get("AZURE_KEY_VAULT_URL", "")

TTL_DAYS = int(os.environ.get("JOB_TTL_DAYS", "7"))
MAX_EVENTS = 100

# ---------------------------------------------------------------------------
# Lazy Azure Clients
# ---------------------------------------------------------------------------

_cosmos_client = None
_blob_service_client = None


def get_cosmos_client():
    global _cosmos_client
    if _cosmos_client is None:
        if not COSMOS_ENDPOINT or not COSMOS_KEY:
            raise RuntimeError("Cosmos DB configuration missing")
        from azure.cosmos import CosmosClient
        _cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    return _cosmos_client


def get_jobs_container():
    client = get_cosmos_client()
    database = client.get_database_client(COSMOS_DATABASE)
    return database.get_container_client(COSMOS_CONTAINER)


def get_blob_service_client():
    global _blob_service_client
    if _blob_service_client is None:
        from azure.storage.blob import BlobServiceClient
        from azure.identity import DefaultAzureCredential

        if RESULTS_CONNECTION_STRING:
            _blob_service_client = BlobServiceClient.from_connection_string(
                RESULTS_CONNECTION_STRING
            )
        elif RESULTS_ACCOUNT_URL:
            _blob_service_client = BlobServiceClient(
                account_url=RESULTS_ACCOUNT_URL,
                credential=DefaultAzureCredential(),
            )
        else:
            raise RuntimeError("Blob storage configuration missing")
    return _blob_service_client


def get_results_container_client():
    from azure.core.exceptions import ResourceExistsError

    client = get_blob_service_client()
    container = client.get_container_client(RESULTS_CONTAINER)
    try:
        container.create_container()
    except ResourceExistsError:
        pass
    return container


def get_service_bus_client():
    from azure.servicebus import ServiceBusClient

    if not SERVICE_BUS_CONNECTION:
        raise RuntimeError("Service Bus connection string missing")
    return ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _expires_at() -> int:
    return int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def _json_response(payload: dict[str, Any], status: int = 200) -> func.HttpResponse:
    headers = {
        "Content-Type": "application/json",
        **_cors_headers(),
    }
    return func.HttpResponse(json.dumps(payload, default=str), status_code=status, headers=headers)


def _cors_preflight() -> func.HttpResponse:
    return func.HttpResponse("", status_code=204, headers=_cors_headers())


def _safe(handler) -> func.HttpResponse:
    try:
        return handler()
    except Exception as exc:
        logger.exception(f"Unhandled request error: {exc}")
        message = "Internal server error"
        if os.environ.get("DEBUG", "").lower() == "true":
            message = f"{message}: {exc}"
        return _json_response({"error": message}, status=500)


def slugify(query: str) -> str:
    import re

    slug = query.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "_", slug)
    slug = slug.strip("_")
    return slug[:100]


def load_openai_api_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    if not (AZURE_KEY_VAULT_URL and OPENAI_API_KEY_SECRET_NAME):
        logger.warning("OPENAI_API_KEY not set and Key Vault not configured")
        return

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=AZURE_KEY_VAULT_URL, credential=credential)
        secret = client.get_secret(OPENAI_API_KEY_SECRET_NAME)
        os.environ["OPENAI_API_KEY"] = secret.value
        logger.info("Loaded OPENAI_API_KEY from Key Vault")
    except Exception as exc:
        logger.error(f"Failed to load OPENAI_API_KEY from Key Vault: {exc}")
        raise


# ---------------------------------------------------------------------------
# Job Helpers (Cosmos)
# ---------------------------------------------------------------------------


def create_job(job_type: str, query: str, payload: dict[str, Any]) -> str:
    job_id = str(uuid.uuid4())
    now = _now_iso()

    job = {
        "id": job_id,
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "query": query,
        "payload": payload,
        "created_at": now,
        "updated_at": now,
        "expires_at": _expires_at(),
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


# ---------------------------------------------------------------------------
# Results Helpers (Blob Storage)
# ---------------------------------------------------------------------------


def _results_path(*parts: str) -> str:
    prefix = f"{RESULTS_PREFIX}/" if RESULTS_PREFIX else ""
    return prefix + "/".join(part.strip("/") for part in parts if part)


def list_result_slugs() -> list[str]:
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        logger.warning("Blob storage not configured; cannot list results")
        return []

    container = get_results_container_client()
    slugs: set[str] = set()
    prefix = _results_path("")

    for blob in container.list_blobs(name_starts_with=prefix):
        parts = blob.name.split("/")
        if len(parts) >= 2:
            slugs.add(parts[1])

    return sorted(slugs)


def get_blob_json(blob_name: str) -> dict[str, Any] | None:
    from azure.core.exceptions import ResourceNotFoundError

    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return None

    container = get_results_container_client()
    try:
        blob_client = container.get_blob_client(blob_name)
        content = blob_client.download_blob().readall().decode("utf-8")
        return json.loads(content)
    except ResourceNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON in blob {blob_name}: {exc}")
        return None


def find_latest_job_for_query(query_slug: str) -> str | None:
    if not RESULTS_CONNECTION_STRING and not RESULTS_ACCOUNT_URL:
        return None

    container = get_results_container_client()
    prefix = _results_path(query_slug)
    job_ids: set[str] = set()

    for blob in container.list_blobs(name_starts_with=f"{prefix}/"):
        parts = blob.name.split("/")
        if len(parts) >= 3:
            job_ids.add(parts[2])

    if not job_ids:
        return None

    return sorted(job_ids)[-1]


def get_query_metadata(query_slug: str) -> dict[str, Any] | None:
    job_id = find_latest_job_for_query(query_slug)
    if not job_id:
        return None

    metadata_blob = _results_path(query_slug, job_id, "metadata.json")
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

    prefix = _results_path(query_slug, job_id)

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


# ---------------------------------------------------------------------------
# Request Parsing
# ---------------------------------------------------------------------------


def _parse_json(req: func.HttpRequest) -> dict[str, Any] | None:
    try:
        return req.get_json()
    except ValueError:
        return None


def _parse_int(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Invalid integer")
    return int(value)


def _parse_float(value: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Invalid float")
    return float(value)


def normalize_pipeline_payload(data: dict[str, Any]) -> dict[str, Any]:
    query = str(data.get("query", "")).strip()
    if not query:
        raise ValueError("Missing required field: query")

    return {
        "query": query,
        "num_results": _parse_int(data.get("num_results"), 5),
        "max_iterations": _parse_int(data.get("max_iterations"), 5),
        "max_accepted": _parse_int(data.get("max_accepted"), 200),
        "top_n": _parse_int(data.get("top_n"), 50),
        "k_factor": _parse_float(data.get("k_factor"), 32.0),
        "pairing": str(data.get("pairing", "swiss")),
        "early_stop": bool(data.get("early_stop", True)),
        "elo_concurrency": _parse_int(data.get("elo_concurrency"), 5),
        "report_top_k": _parse_int(data.get("report_top_k"), 30),
    }


def normalize_search_payload(data: dict[str, Any]) -> dict[str, Any]:
    query = str(data.get("query", "")).strip()
    if not query:
        raise ValueError("Missing required field: query")

    return {
        "query": query,
        "num_results": _parse_int(data.get("num_results"), 5),
        "max_iterations": _parse_int(data.get("max_iterations"), 5),
        "max_accepted": _parse_int(data.get("max_accepted"), 200),
        "top_n": _parse_int(data.get("top_n"), 50),
    }


# ---------------------------------------------------------------------------
# HTTP API Endpoints
# ---------------------------------------------------------------------------


@app.route(route="health", methods=["GET", "OPTIONS"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    return _safe(lambda: _json_response({"status": "ok", "version": "0.1.0"}))


@app.route(route="", methods=["GET", "OPTIONS"])
def root(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    return _safe(lambda: _json_response({
        "message": "PaperPilot API (Azure Functions)",
        "version": "0.1.0",
        "endpoints": {
            "health": "GET /api/health",
            "create_pipeline": "POST /api/pipeline",
            "create_search": "POST /api/search",
            "create_job": "POST /api/jobs",
            "get_job": "GET /api/jobs/{job_id}",
            "pipeline_status": "GET /api/pipeline/{job_id}",
            "results": "GET /api/results",
        },
    }))


@app.route(route="jobs", methods=["POST", "OPTIONS"])
def create_job_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        data = _parse_json(req)
        if data is None:
            return _json_response({"error": "Invalid JSON body"}, status=400)

        job_type = str(data.get("job_type", "pipeline"))
        try:
            if job_type == "pipeline":
                payload = normalize_pipeline_payload(data)
            elif job_type == "search":
                payload = normalize_search_payload(data)
            else:
                payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
                query = data.get("query")
                if query:
                    payload["query"] = query
                if "query" not in payload:
                    raise ValueError("Missing required field: query")
        except ValueError as exc:
            return _json_response({"error": str(exc)}, status=400)

        job_id = create_job(job_type=job_type, query=payload["query"], payload=payload)
        enqueue_job(job_id, job_type, payload)

        return _json_response(
            {
                "job_id": job_id,
                "status": "queued",
                "message": "Job created and queued for processing",
            },
            status=202,
        )

    return _safe(handler)


@app.route(route="pipeline", methods=["POST", "OPTIONS"])
def start_pipeline(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        data = _parse_json(req)
        if data is None:
            return _json_response({"error": "Invalid JSON body"}, status=400)

        try:
            payload = normalize_pipeline_payload(data)
        except ValueError as exc:
            return _json_response({"error": str(exc)}, status=400)

        job_id = create_job("pipeline", payload["query"], payload)
        enqueue_job(job_id, "pipeline", payload)

        return _json_response(
            {
                "job_id": job_id,
                "status": "queued",
                "message": "Pipeline job queued for processing",
            },
            status=202,
        )

    return _safe(handler)


@app.route(route="search", methods=["POST", "OPTIONS"])
def start_search(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        data = _parse_json(req)
        if data is None:
            return _json_response({"error": "Invalid JSON body"}, status=400)

        try:
            payload = normalize_search_payload(data)
        except ValueError as exc:
            return _json_response({"error": str(exc)}, status=400)

        job_id = create_job("search", payload["query"], payload)
        enqueue_job(job_id, "search", payload)

        return _json_response(
            {
                "job_id": job_id,
                "status": "queued",
                "message": "Search job queued for processing",
            },
            status=202,
        )

    return _safe(handler)


@app.route(route="jobs/{job_id}", methods=["GET", "OPTIONS"])
def get_job_status(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        job_id = req.route_params.get("job_id")
        if not job_id:
            return _json_response({"error": "Missing job_id"}, status=400)

        job = get_job(job_id)
        if not job:
            return _json_response({"error": "Job not found"}, status=404)

        return _json_response({
            "job_id": job.get("job_id"),
            "job_type": job.get("job_type", "unknown"),
            "status": job.get("status", "unknown"),
            "query": job.get("query", ""),
            "created_at": job.get("created_at", ""),
            "updated_at": job.get("updated_at", ""),
            "progress": job.get("progress"),
            "result": job.get("result"),
            "error_message": job.get("error_message"),
        })

    return _safe(handler)


@app.route(route="pipeline/{job_id}", methods=["GET", "OPTIONS"])
def get_pipeline_status(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        job_id = req.route_params.get("job_id")
        if not job_id:
            return _json_response({"error": "Missing job_id"}, status=400)

        job = get_job(job_id)
        if not job:
            return _json_response({"error": "Job not found"}, status=404)

        internal_status = job.get("status", "unknown")
        progress = job.get("progress", {}) or {}
        phase = progress.get("phase", "")

        if internal_status == "running":
            if phase == "search":
                frontend_status = "searching"
            elif phase == "ranking":
                frontend_status = "ranking"
            elif phase in {"report", "upload"}:
                frontend_status = "reporting"
            else:
                frontend_status = "searching"
        else:
            frontend_status = internal_status

        return _json_response({
            "job_id": job.get("job_id"),
            "status": frontend_status,
            "query": job.get("query", ""),
            "phase": phase or None,
            "phase_step": progress.get("step"),
            "phase_step_name": progress.get("step_name") or progress.get("phase"),
            "phase_progress": progress.get("current"),
            "phase_total": progress.get("total"),
            "progress_message": progress.get("message"),
            "papers": (job.get("result") or {}).get("top_papers"),
            "report_data": None,
            "error": job.get("error_message"),
        })

    return _safe(handler)


@app.route(route="results", methods=["GET", "OPTIONS"])
def list_results(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    return _safe(lambda: _json_response({
        "queries": [slug.replace("_", " ").title() for slug in list_result_slugs()]
    }))


@app.route(route="results/{query_slug}", methods=["GET", "OPTIONS"])
def get_results_metadata(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        query_slug = req.route_params.get("query_slug")
        if not query_slug:
            return _json_response({"error": "Missing query"}, status=400)

        metadata = get_query_metadata(query_slug)
        if not metadata:
            return _json_response({"error": f"No results found for query: {query_slug}"}, status=404)

        return _json_response({
            "query": query_slug,
            "metadata": metadata,
        })

    return _safe(handler)


@app.route(route="results/{query_slug}/all", methods=["GET", "OPTIONS"])
def get_all_results(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        query_slug = req.route_params.get("query_slug")
        if not query_slug:
            return _json_response({"error": "Missing query"}, status=400)

        results = get_query_results(query_slug)

        if not results["report"] and not results["snowball"]:
            return _json_response({"error": f"No results found for query: {query_slug}"}, status=404)

        return _json_response(results)

    return _safe(handler)


@app.route(route="results/{query_slug}/report", methods=["GET", "OPTIONS"])
def get_report_results(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    def handler():
        query_slug = req.route_params.get("query_slug")
        if not query_slug:
            return _json_response({"error": "Missing query"}, status=400)

        results = get_query_results(query_slug)
        if not results["report"]:
            return _json_response({"error": f"No report found for query: {query_slug}"}, status=404)

        return _json_response(results["report"])

    return _safe(handler)


# ---------------------------------------------------------------------------
# Service Bus Worker
# ---------------------------------------------------------------------------


def append_event(events: list[dict[str, Any]], event_type: str, phase: str, message: str, **kwargs) -> list[dict[str, Any]]:
    event = {
        "ts": _now_iso(),
        "type": event_type,
        "phase": phase,
        "message": message,
        **kwargs,
    }
    events.append(event)
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]
    return events


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
        "updated_at": _now_iso(),
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
        logger.warning(f"Job {job_id} not found while updating progress")


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
    from paperpilot.core.elo_ranker import EloRanker, RankerConfig
    from paperpilot.core.models import SnowballCandidate
    from paperpilot.core.profiler import generate_query_profile
    from paperpilot.core.report.generator import generate_report, report_to_dict
    from paperpilot.core.service import run_search

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

    workspace = Path(tempfile.mkdtemp(prefix=f"paperpilot_{job_id}_"))
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
            "created_at": _now_iso(),
            "last_updated": _now_iso(),
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

        blob_prefix = _results_path(query_slug, job_id)
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
            logger.warning(f"Failed to cleanup workspace {workspace}: {exc}")


async def run_search_job(job_id: str, payload: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    from paperpilot.core.service import run_search

    query = payload.get("query", "")
    num_results = payload.get("num_results", 5)
    max_iterations = payload.get("max_iterations", 5)
    max_accepted = payload.get("max_accepted", 200)
    top_n = payload.get("top_n", 50)

    query_slug = slugify(query)
    workspace = Path(tempfile.mkdtemp(prefix=f"paperpilot_{job_id}_"))
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
            "created_at": _now_iso(),
            "last_updated": _now_iso(),
            "query": query,
        }
        metadata_path = results_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        blob_prefix = _results_path(query_slug, job_id)
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
            logger.warning(f"Failed to cleanup workspace {workspace}: {exc}")


def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    events = append_event(events, "job_start", "init", f"Starting {job_type} job")
    update_job_progress(job_id, "running", "init", 0, "Initializing...", events=events)

    load_openai_api_key()

    if job_type == "pipeline":
        return asyncio.run(run_pipeline(job_id, payload, events))
    if job_type == "search":
        return asyncio.run(run_search_job(job_id, payload, events))

    raise ValueError(f"Unknown job type: {job_type}")


@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name=QUEUE_NAME,
    connection="AZURE_SERVICE_BUS_CONNECTION_STRING",
)
def process_job_message(msg: func.ServiceBusMessage):
    body = msg.get_body().decode("utf-8")
    logger.info(f"Processing message: {body}")

    job_id = None
    try:
        payload = json.loads(body)
        job_id = payload.get("job_id")
        job_type = payload.get("job_type")
        job_payload = payload.get("payload") or {}

        if not job_id or not job_type:
            logger.error("Invalid message: missing job_id or job_type")
            return

        result = process_job(job_id, job_type, job_payload)
        update_job_progress(job_id, "completed", "complete", 0, "Job completed", result=result)

    except Exception as exc:
        logger.exception(f"Error processing message for job {job_id}: {exc}")
        if job_id:
            update_job_progress(job_id, "failed", "error", 0, f"Job failed: {exc}", error=str(exc))
        raise
