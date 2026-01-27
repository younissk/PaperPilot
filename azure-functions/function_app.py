"""
PaperPilot Azure Functions - Demo Stub

This is a minimal Azure Functions app demonstrating:
1. HTTP trigger for API endpoints
2. Service Bus trigger for background job processing
3. Integration with Cosmos DB for job state

Uses the v2 programming model (Python 3.9+) with decorators.
"""

import azure.functions as func
import logging
import json
import os
import uuid
from datetime import datetime, UTC

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ============================================================================
# Configuration
# ============================================================================

COSMOS_ENDPOINT = os.environ.get("AZURE_COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("AZURE_COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("AZURE_COSMOS_DATABASE", "paperpilot")
COSMOS_CONTAINER = os.environ.get("AZURE_COSMOS_CONTAINER", "jobs")

SERVICE_BUS_CONNECTION = os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING", "")
QUEUE_NAME = os.environ.get("AZURE_SERVICE_BUS_QUEUE_NAME", "paperpilot-jobs")


# ============================================================================
# Helper Functions
# ============================================================================

def get_cosmos_client():
    """Lazy-load Cosmos client to avoid import errors if not configured."""
    from azure.cosmos import CosmosClient
    return CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)


def get_jobs_container():
    """Get the Cosmos DB jobs container."""
    client = get_cosmos_client()
    database = client.get_database_client(COSMOS_DATABASE)
    return database.get_container_client(COSMOS_CONTAINER)


def get_service_bus_client():
    """Get the Service Bus client."""
    from azure.servicebus import ServiceBusClient
    return ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION)


# ============================================================================
# HTTP Triggers - API Endpoints
# ============================================================================

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint - GET /api/health"""
    logging.info("Health check requested")
    
    response = {
        "status": "ok",
        "service": "paperpilot-api",
        "version": "0.1.0-azure-stub",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    
    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )


@app.route(route="", methods=["GET"])
def root(req: func.HttpRequest) -> func.HttpResponse:
    """Root endpoint - GET /api/"""
    return func.HttpResponse(
        json.dumps({
            "message": "PaperPilot API (Azure Functions Stub)",
            "version": "0.1.0",
            "endpoints": {
                "health": "GET /api/health",
                "create_job": "POST /api/jobs",
                "get_job": "GET /api/jobs/{job_id}",
            }
        }),
        status_code=200,
        mimetype="application/json"
    )


@app.route(route="jobs", methods=["POST"])
def create_job(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new job - POST /api/jobs
    
    Request body:
    {
        "query": "research topic",
        "job_type": "pipeline"  // optional, defaults to "pipeline"
    }
    """
    logging.info("Create job requested")
    
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json"
        )
    
    query = req_body.get("query")
    if not query:
        return func.HttpResponse(
            json.dumps({"error": "Missing required field: query"}),
            status_code=400,
            mimetype="application/json"
        )
    
    job_type = req_body.get("job_type", "pipeline")
    job_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    
    # Create job document
    job = {
        "id": job_id,
        "job_id": job_id,  # partition key
        "job_type": job_type,
        "status": "queued",
        "query": query,
        "created_at": now,
        "updated_at": now,
        "progress": {
            "phase": "init",
            "step": 0,
            "message": "Waiting to start..."
        }
    }
    
    try:
        # Save to Cosmos DB
        container = get_jobs_container()
        container.create_item(job)
        logging.info(f"Job {job_id} created in Cosmos DB")
        
        # Send message to Service Bus queue
        from azure.servicebus import ServiceBusMessage
        with get_service_bus_client() as sb_client:
            with sb_client.get_queue_sender(QUEUE_NAME) as sender:
                message = ServiceBusMessage(
                    json.dumps({
                        "job_id": job_id,
                        "job_type": job_type,
                        "query": query,
                    })
                )
                sender.send_messages(message)
                logging.info(f"Job {job_id} sent to Service Bus queue")
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "status": "queued",
                "message": "Job created and queued for processing"
            }),
            status_code=202,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error creating job: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to create job: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="jobs/{job_id}", methods=["GET"])
def get_job(req: func.HttpRequest) -> func.HttpResponse:
    """Get job status - GET /api/jobs/{job_id}"""
    job_id = req.route_params.get("job_id")
    logging.info(f"Get job requested: {job_id}")
    
    if not job_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing job_id"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        container = get_jobs_container()
        job = container.read_item(item=job_id, partition_key=job_id)
        
        return func.HttpResponse(
            json.dumps(job),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        if "NotFound" in str(e):
            return func.HttpResponse(
                json.dumps({"error": "Job not found"}),
                status_code=404,
                mimetype="application/json"
            )
        logging.error(f"Error getting job: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get job: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


# ============================================================================
# Service Bus Trigger - Background Worker
# ============================================================================

@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="paperpilot-jobs",
    connection="AZURE_SERVICE_BUS_CONNECTION_STRING"
)
def process_job(msg: func.ServiceBusMessage):
    """Process jobs from Service Bus queue.
    
    This is the worker function that processes pipeline jobs.
    For now, it's a stub that just updates the job status.
    """
    message_body = msg.get_body().decode("utf-8")
    logging.info(f"Processing message: {message_body}")
    
    try:
        payload = json.loads(message_body)
        job_id = payload.get("job_id")
        job_type = payload.get("job_type")
        query = payload.get("query")
        
        logging.info(f"Processing job {job_id} of type {job_type}: {query}")
        
        # Update job status to running
        container = get_jobs_container()
        
        # Read current job
        job = container.read_item(item=job_id, partition_key=job_id)
        
        # Update to running
        job["status"] = "running"
        job["updated_at"] = datetime.now(UTC).isoformat()
        job["progress"] = {
            "phase": "processing",
            "step": 1,
            "message": "Job is being processed (stub)..."
        }
        container.replace_item(item=job_id, body=job)
        logging.info(f"Job {job_id} status updated to running")
        
        # =====================================================================
        # TODO: Actual processing would happen here
        # For the stub, we just simulate completion
        # =====================================================================
        
        # Update to completed
        job["status"] = "completed"
        job["updated_at"] = datetime.now(UTC).isoformat()
        job["progress"] = {
            "phase": "complete",
            "step": 2,
            "message": "Job completed successfully (stub)"
        }
        job["result"] = {
            "message": "This is a stub result",
            "papers_found": 0,
            "note": "Real implementation coming soon!"
        }
        container.replace_item(item=job_id, body=job)
        logging.info(f"Job {job_id} completed")
        
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        
        # Try to update job status to failed
        try:
            if job_id:
                container = get_jobs_container()
                job = container.read_item(item=job_id, partition_key=job_id)
                job["status"] = "failed"
                job["updated_at"] = datetime.now(UTC).isoformat()
                job["error_message"] = str(e)
                container.replace_item(item=job_id, body=job)
        except Exception:
            pass
        
        raise  # Re-raise to trigger retry/dead-letter
