"""AWS Lambda handler for PaperPilot API (Minimal Serverless Version).

This is a lightweight API that handles:
- Health checks
- Job creation (writes to DynamoDB, sends to SQS)
- Job status queries (reads from DynamoDB)

Heavy processing is delegated to the Worker Lambda via SQS.
This keeps the API Lambda small and fast for cold starts.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from mangum import Mangum

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

# TTL for jobs (7 days)
TTL_DAYS = 7


# ==============================================================================
# Pydantic Models
# ==============================================================================

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None


class JobCreateResponse(BaseModel):
    """Response when a job is created."""
    job_id: str
    status: str = "queued"
    message: str = "Job queued for processing"


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
    now = datetime.now(timezone.utc).isoformat()
    expires_at = int((datetime.now(timezone.utc) + timedelta(days=TTL_DAYS)).timestamp())
    
    item = {
        "job_id": job_id,
        "job_type": job_type,
        "status": JobStatus.QUEUED.value,
        "query": query,
        "payload": payload,
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


def get_job(job_id: str) -> Optional[dict]:
    """Get job from DynamoDB."""
    try:
        response = jobs_table.get_item(Key={"job_id": job_id})
        return response.get("Item")
    except ClientError as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return None


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


# ==============================================================================
# Lambda Handler
# ==============================================================================

handler = Mangum(app, lifespan="off")
