"""AWS Lambda handler for PaperPilot API (Minimal Serverless Version).

This is a lightweight API that handles:
- Health checks
- Job creation (writes to DynamoDB, sends to SQS)
- Job status queries (reads from DynamoDB)
- Results queries (reads from S3)

Heavy processing is delegated to the Worker Lambda via SQS.
This keeps the API Lambda small and fast for cold starts.
"""

import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, Field

# Import shared utilities from paperpilot package
# (vendored at build time via buildspec.yml)
from paperpilot.aws import JobStatus, convert_decimal_to_native, convert_floats_to_decimal

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment configuration
JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "")
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "")  # For LocalStack

# Initialize AWS clients (with optional LocalStack endpoint for local dev)
boto_kwargs: dict[str, str] = {}
if AWS_ENDPOINT_URL:
    logger.info(f"Using custom AWS endpoint: {AWS_ENDPOINT_URL}")
    boto_kwargs["endpoint_url"] = AWS_ENDPOINT_URL

dynamodb = boto3.resource("dynamodb", **boto_kwargs)
sqs = boto3.client("sqs", **boto_kwargs)
s3_client = boto3.client("s3", **boto_kwargs)
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

# TTL for jobs (7 days)
TTL_DAYS = 7


# ==============================================================================
# Pydantic Models
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class PipelineRequest(BaseModel):
    """Request to start a full pipeline job."""
    query: str = Field(..., description="Research topic to search for")
    num_results: int = Field(5, ge=1, le=100)
    max_iterations: int = Field(5, ge=1, le=20)
    max_accepted: int = Field(200, ge=10)
    top_n: int = Field(50, ge=5)
    k_factor: float = Field(32.0, ge=1.0, le=100.0)
    pairing: str = Field("swiss")
    early_stop: bool = Field(True)
    elo_concurrency: int = Field(5, ge=1, le=20)
    report_top_k: int = Field(30, ge=1)


class SearchRequest(BaseModel):
    """Request to start a search job."""
    query: str = Field(..., description="Research topic to search for")
    num_results: int = Field(5, ge=1, le=100)
    max_iterations: int = Field(5, ge=1, le=20)
    max_accepted: int = Field(200, ge=10)
    top_n: int = Field(50, ge=5)


class JobResponse(BaseModel):
    """Response for job status."""
    job_id: str
    job_type: str
    status: str
    query: str
    created_at: str
    updated_at: str
    progress: dict | None = None
    result: dict | None = None
    error_message: str | None = None


class JobCreateResponse(BaseModel):
    """Response when a job is created."""
    job_id: str
    status: str = "queued"
    message: str = "Job queued for processing"


class PipelineStatusResponse(BaseModel):
    """Response for pipeline job status (frontend-compatible format).
    
    This maps the DynamoDB job format to the format expected by the frontend.
    See docs/API_CONTRACT.md for details.
    """
    job_id: str
    status: str  # queued, searching, ranking, reporting, completed, failed
    query: str
    phase: str | None = None
    phase_step: int | None = None
    phase_step_name: str | None = None
    phase_progress: int | None = None
    phase_total: int | None = None
    progress_message: str | None = None
    papers: list | None = None
    report_data: dict | None = None
    error: str | None = None


# ==============================================================================
# FastAPI App
# ==============================================================================

app = FastAPI(
    title="PaperPilot API",
    description="AI-powered academic literature discovery (Serverless)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Helper Functions
# ==============================================================================

def create_job(job_type: str, query: str, payload: dict) -> str:
    """Create a job in DynamoDB and return job_id."""
    job_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    expires_at = int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())

    # Convert floats to Decimals for DynamoDB compatibility
    safe_payload = convert_floats_to_decimal(payload)

    item = {
        "job_id": job_id,
        "job_type": job_type,
        "status": JobStatus.QUEUED.value,
        "query": query,
        "payload": safe_payload,
        "created_at": now,
        "updated_at": now,
        "expires_at": expires_at,
        "progress": {"step": 0, "message": "Waiting to start..."},
    }

    jobs_table.put_item(Item=item)
    return job_id


def enqueue_job(job_id: str, job_type: str, payload: dict) -> None:
    """Send job message to SQS."""
    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not set, skipping queue")
        return

    message_body = json.dumps({
        "job_id": job_id,
        "job_type": job_type,
        "payload": payload,
    })

    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=message_body,
    )


def get_job(job_id: str) -> dict | None:
    """Get job from DynamoDB."""
    try:
        response = jobs_table.get_item(Key={"job_id": job_id})
        return response.get("Item")
    except ClientError as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return None


def list_s3_query_slugs() -> list[str]:
    """List all query slugs from S3 results folder."""
    if not RESULTS_BUCKET:
        logger.warning("RESULTS_BUCKET not set, cannot list queries")
        return []

    try:
        # List "directories" under results/
        response = s3_client.list_objects_v2(
            Bucket=RESULTS_BUCKET,
            Prefix="results/",
            Delimiter="/"
        )

        slugs = []
        for prefix in response.get("CommonPrefixes", []):
            # Extract slug from "results/{slug}/"
            path = prefix.get("Prefix", "")
            parts = path.strip("/").split("/")
            if len(parts) >= 2:
                slugs.append(parts[1])

        return slugs
    except ClientError as e:
        logger.error(f"Error listing S3 queries: {e}")
        return []


def get_s3_json(key: str) -> dict | None:
    """Get JSON file from S3."""
    if not RESULTS_BUCKET:
        return None

    try:
        response = s3_client.get_object(Bucket=RESULTS_BUCKET, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        logger.error(f"Error getting S3 object {key}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from {key}: {e}")
        return None


def find_latest_job_for_query(query_slug: str) -> str | None:
    """Find the most recent job_id for a query slug in S3."""
    if not RESULTS_BUCKET:
        return None

    try:
        # List objects under results/{query_slug}/
        response = s3_client.list_objects_v2(
            Bucket=RESULTS_BUCKET,
            Prefix=f"results/{query_slug}/",
            Delimiter="/"
        )

        # Find job_id prefixes (format: results/{slug}/{job_id}/)
        job_ids = []
        for prefix in response.get("CommonPrefixes", []):
            path = prefix.get("Prefix", "")
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                job_ids.append(parts[2])

        if not job_ids:
            return None

        # Return the most recent (by UUID, which has timestamp component)
        # For proper ordering, we'd need to check metadata.json
        return sorted(job_ids)[-1]
    except ClientError as e:
        logger.error(f"Error finding jobs for query {query_slug}: {e}")
        return None


def get_query_results(query_slug: str) -> dict:
    """Get all available results for a query from S3."""
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

    prefix = f"results/{query_slug}/{job_id}"

    # Try to get each file type
    report = get_s3_json(f"{prefix}/report_top_k30.json")
    if not report:
        # Try other common report filenames
        for k in [20, 50, 10]:
            report = get_s3_json(f"{prefix}/report_top_k{k}.json")
            if report:
                break
    result["report"] = report

    result["snowball"] = get_s3_json(f"{prefix}/snowball.json")

    # These are optional
    result["graph"] = get_s3_json(f"{prefix}/graph.json")
    result["timeline"] = get_s3_json(f"{prefix}/timeline.json")
    result["clusters"] = get_s3_json(f"{prefix}/clusters.json")

    return result


def get_query_metadata(query_slug: str) -> dict | None:
    """Get metadata for a query from S3."""
    job_id = find_latest_job_for_query(query_slug)

    if not job_id:
        return None

    metadata = get_s3_json(f"results/{query_slug}/{job_id}/metadata.json")
    return metadata


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "PaperPilot API (Serverless)",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "create_pipeline": "POST /api/pipeline",
            "create_search": "POST /api/search",
            "get_job": "GET /api/jobs/{job_id}",
        }
    }


@app.post("/api/pipeline", response_model=JobCreateResponse, status_code=202, tags=["pipeline"])
async def start_pipeline(request: PipelineRequest):
    """Start a full pipeline job (search + ranking + report)."""
    payload = request.model_dump()

    job_id = create_job(
        job_type="pipeline",
        query=request.query,
        payload=payload,
    )

    enqueue_job(job_id, "pipeline", payload)

    return JobCreateResponse(
        job_id=job_id,
        status="queued",
        message="Pipeline job queued for processing",
    )


@app.post("/api/search", response_model=JobCreateResponse, status_code=202, tags=["search"])
async def start_search(request: SearchRequest):
    """Start a search job."""
    payload = request.model_dump()

    job_id = create_job(
        job_type="search",
        query=request.query,
        payload=payload,
    )

    enqueue_job(job_id, "search", payload)

    return JobCreateResponse(
        job_id=job_id,
        status="queued",
        message="Search job queued for processing",
    )


@app.get("/api/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
async def get_job_status(job_id: str):
    """Get job status by ID."""
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Convert Decimals back to native types for JSON serialization
    job = convert_decimal_to_native(job)

    return JobResponse(
        job_id=job["job_id"],
        job_type=job.get("job_type", "unknown"),
        status=job.get("status", "unknown"),
        query=job.get("query", ""),
        created_at=job.get("created_at", ""),
        updated_at=job.get("updated_at", ""),
        progress=job.get("progress"),
        result=job.get("result"),
        error_message=job.get("error_message"),
    )


@app.get("/api/pipeline/{job_id}", response_model=PipelineStatusResponse, tags=["pipeline"])
async def get_pipeline_status(job_id: str):
    """Get pipeline job status in frontend-compatible format.
    
    This endpoint maps the internal DynamoDB job format to the format
    expected by the Astro frontend for progress polling.
    See docs/API_CONTRACT.md for details.
    """
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Convert Decimals back to native types for JSON serialization
    job = convert_decimal_to_native(job)

    # Map internal status to frontend status
    internal_status = job.get("status", "unknown")
    progress = job.get("progress", {})
    phase = progress.get("phase", "")

    # Map 'running' status to phase-specific status for frontend
    if internal_status == "running":
        if phase == "search":
            frontend_status = "searching"
        elif phase == "ranking":
            frontend_status = "ranking"
        elif phase == "report":
            frontend_status = "reporting"
        elif phase == "upload":
            frontend_status = "reporting"  # Treat upload as part of reporting
        else:
            frontend_status = "searching"  # Default for running state
    else:
        frontend_status = internal_status  # queued, completed, failed pass through

    return PipelineStatusResponse(
        job_id=job["job_id"],
        status=frontend_status,
        query=job.get("query", ""),
        phase=phase if phase else None,
        phase_step=progress.get("step"),
        phase_step_name=progress.get("phase"),  # Using phase as step name
        phase_progress=progress.get("current"),
        phase_total=progress.get("total"),
        progress_message=progress.get("message"),
        papers=job.get("result", {}).get("top_papers") if job.get("result") else None,
        report_data=None,  # Report data is fetched separately via /api/results
        error=job.get("error_message"),
    )


# ==============================================================================
# Results Endpoints (reads from S3)
# ==============================================================================

@app.get("/api/results", tags=["results"])
async def list_results():
    """List all available query slugs with results.
    
    Returns a list of query slugs that have completed pipeline results in S3.
    """
    slugs = list_s3_query_slugs()

    # Convert slugs back to readable query format
    queries = [slug.replace("_", " ").title() for slug in slugs]

    return {"queries": queries}


@app.get("/api/results/{query_slug}", tags=["results"])
async def get_results_metadata(query_slug: str):
    """Get metadata for a specific query.
    
    Returns metadata about the query results including file paths and timestamps.
    """
    metadata = get_query_metadata(query_slug)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"No results found for query: {query_slug}")

    return {
        "query": query_slug,
        "metadata": metadata,
    }


@app.get("/api/results/{query_slug}/all", tags=["results"])
async def get_all_results(query_slug: str):
    """Get all results for a query (report, snowball, graph, timeline, clusters).
    
    This is the main endpoint used by the report page to fetch all data.
    """
    results = get_query_results(query_slug)

    # If no results at all, return 404
    if not results["report"] and not results["snowball"]:
        raise HTTPException(status_code=404, detail=f"No results found for query: {query_slug}")

    return results


@app.get("/api/results/{query_slug}/report", tags=["results"])
async def get_report_results(query_slug: str):
    """Get just the report for a query.
    
    Returns the generated research report.
    """
    results = get_query_results(query_slug)

    if not results["report"]:
        raise HTTPException(status_code=404, detail=f"No report found for query: {query_slug}")

    return results["report"]


# ==============================================================================
# Lambda Handler
# ==============================================================================

handler = Mangum(app, lifespan="off")
