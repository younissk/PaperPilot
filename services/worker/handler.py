"""AWS Lambda handler for PaperPilot Worker (SQS consumer).

Processes job messages from the SQS queue and updates job state in DynamoDB.
Implements the full pipeline: Search → Rank → Report.
Artifacts are stored in S3, job state/progress in DynamoDB.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Import shared utilities from paperpilot package
# (vendored at build time via buildspec.yml)
from paperpilot.aws import JobStatus, convert_floats_to_decimal, slugify

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment configuration
JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "paperpilot-jobs-prod")
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "")
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "")  # For LocalStack
OPENAI_API_KEY_SECRET_ARN = os.environ.get("OPENAI_API_KEY_SECRET_ARN", "")

# Initialize AWS clients (with optional LocalStack endpoint for local dev)
boto_kwargs: dict[str, str] = {}
if AWS_ENDPOINT_URL:
    logger.info(f"Using custom AWS endpoint: {AWS_ENDPOINT_URL}")
    boto_kwargs["endpoint_url"] = AWS_ENDPOINT_URL

dynamodb = boto3.resource("dynamodb", **boto_kwargs)
s3_client = boto3.client("s3", **boto_kwargs)
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)


def _load_openai_api_key_from_secrets_manager() -> None:
    """Load OpenAI API key from Secrets Manager and set as environment variable.
    
    This is called once at module load time (Lambda cold start).
    The key is cached in the environment for subsequent invocations.
    """
    # Skip if already set (either manually or from previous invocation)
    if os.environ.get("OPENAI_API_KEY"):
        logger.info("OPENAI_API_KEY already set in environment")
        return

    # Skip if no secret ARN configured
    if not OPENAI_API_KEY_SECRET_ARN:
        logger.warning("OPENAI_API_KEY_SECRET_ARN not set, skipping Secrets Manager lookup")
        return

    try:
        logger.info(f"Fetching OpenAI API key from Secrets Manager: {OPENAI_API_KEY_SECRET_ARN}")
        secrets_client = boto3.client("secretsmanager", **boto_kwargs)
        response = secrets_client.get_secret_value(SecretId=OPENAI_API_KEY_SECRET_ARN)

        # Secret can be either a plain string or JSON
        secret_value = response.get("SecretString", "")

        # Try parsing as JSON (common pattern: {"OPENAI_API_KEY": "sk-..."})
        try:
            secret_dict = json.loads(secret_value)
            # Look for common key names
            api_key = (
                secret_dict.get("OPENAI_API_KEY") or
                secret_dict.get("openai_api_key") or
                secret_dict.get("api_key") or
                secret_dict.get("key")
            )
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                logger.info("Successfully loaded OPENAI_API_KEY from Secrets Manager (JSON format)")
                return
        except json.JSONDecodeError:
            pass

        # Treat as plain string (the secret value IS the API key)
        if secret_value and secret_value.startswith("sk-"):
            os.environ["OPENAI_API_KEY"] = secret_value
            logger.info("Successfully loaded OPENAI_API_KEY from Secrets Manager (plain string)")
            return

        logger.error("Secret does not contain a valid OpenAI API key")

    except ClientError as e:
        logger.error(f"Failed to fetch secret from Secrets Manager: {e}")
        raise


# Load the API key at module initialization (Lambda cold start)
_load_openai_api_key_from_secrets_manager()

# Maximum number of events to store in DynamoDB (bounded list for real-time UX later)
MAX_EVENTS = 100


def append_event(events: list[dict], event_type: str, phase: str, message: str, **kwargs) -> list[dict]:
    """Append an event to the events list, keeping it bounded."""
    event = {
        "ts": datetime.now(UTC).isoformat(),
        "type": event_type,
        "phase": phase,
        "message": message,
        **kwargs
    }
    events.append(event)
    # Keep only last MAX_EVENTS
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
    events: list[dict] | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Update job progress in DynamoDB with detailed progress tracking."""
    progress = convert_floats_to_decimal({
        "phase": phase,
        "step": step,
        "message": message,
        "current": current,
        "total": total,
    })

    update_expr = "SET #status = :status, updated_at = :updated_at, progress = :progress"
    expr_names = {"#status": "status"}
    expr_values = {
        ":status": status,
        ":updated_at": datetime.now(UTC).isoformat(),
        ":progress": progress,
    }

    if events is not None:
        update_expr += ", events = :events"
        expr_values[":events"] = convert_floats_to_decimal(events)

    if result is not None:
        update_expr += ", #result = :result"
        expr_names["#result"] = "result"
        expr_values[":result"] = convert_floats_to_decimal(result)

    if error is not None:
        update_expr += ", error_message = :error"
        expr_values[":error"] = error

    try:
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        logger.info(f"Updated job {job_id}: phase={phase}, step={step}, message={message}")
    except ClientError as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        raise


def upload_artifacts_to_s3(local_dir: Path, bucket: str, prefix: str) -> list[dict]:
    """Upload all files from local_dir to S3 and return artifact metadata."""
    artifacts = []

    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_dir)
            s3_key = f"{prefix}/{relative_path}"

            # Determine content type
            content_type = "application/json"
            if file_path.suffix == ".html":
                content_type = "text/html"
            elif file_path.suffix == ".txt":
                content_type = "text/plain"

            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket,
                    s3_key,
                    ExtraArgs={"ContentType": content_type}
                )

                file_size = file_path.stat().st_size
                artifacts.append({
                    "key": s3_key,
                    "size": file_size,
                    "content_type": content_type,
                })
                logger.info(f"Uploaded {s3_key} ({file_size} bytes)")
            except ClientError as e:
                logger.error(f"Failed to upload {s3_key}: {e}")
                raise

    return artifacts


async def run_pipeline(job_id: str, payload: dict[str, Any], events: list[dict]) -> dict[str, Any]:
    """Run the full pipeline: Search → Rank → Report.
    
    Args:
        job_id: Unique job identifier
        payload: Pipeline parameters (query, num_results, etc.)
        events: Events list to append progress events to
        
    Returns:
        Result dict with S3 pointers and summary
    """
    # Import core modules here to avoid import errors if deps missing
    from paperpilot.core.elo_ranker import EloRanker, RankerConfig
    from paperpilot.core.models import SnowballCandidate
    from paperpilot.core.profiler import generate_query_profile
    from paperpilot.core.report.generator import generate_report, report_to_dict
    from paperpilot.core.service import run_search

    # Extract parameters
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

    # Create workspace in /tmp
    workspace = Path(tempfile.mkdtemp(prefix=f"paperpilot_{job_id}_"))
    results_dir = workspace / query_slug
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        # =========================================================================
        # PHASE 1: SEARCH
        # =========================================================================
        events = append_event(events, "phase_start", "search", "Starting search phase")
        update_job_progress(job_id, JobStatus.RUNNING.value, "search", 0, "Starting search...", events=events)

        snowball_path = results_dir / "snowball.json"

        def search_progress_callback(step, step_name, current, total, message, curr_iter, total_iter):
            nonlocal events
            events = append_event(events, "progress", "search", message, step=step, step_name=step_name)
            update_job_progress(
                job_id, JobStatus.RUNNING.value, "search", step, message,
                current=current, total=total, events=events
            )

        logger.info(f"Starting search for query: {query}")
        accepted_papers = await run_search(
            query=query,
            num_results=num_results,
            output_file=str(snowball_path),
            max_iterations=max_iterations,
            max_accepted=max_accepted,
            top_n=top_n,
            progress_callback=search_progress_callback,
        )

        events = append_event(events, "phase_complete", "search", f"Search complete: found {len(accepted_papers)} papers")
        update_job_progress(
            job_id, JobStatus.RUNNING.value, "search", 6,
            f"Search complete: {len(accepted_papers)} papers", events=events
        )

        if not accepted_papers:
            raise ValueError("No papers found during search")

        # =========================================================================
        # PHASE 2: RANKING (ELO)
        # =========================================================================
        events = append_event(events, "phase_start", "ranking", "Starting ELO ranking phase")
        update_job_progress(job_id, JobStatus.RUNNING.value, "ranking", 0, "Starting ranking...", events=events)

        # Convert AcceptedPaper to SnowballCandidate for ranker
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

        # Generate query profile for ranking
        profile = await generate_query_profile(query)

        # Configure ranker
        ranker_config = RankerConfig(
            k_factor=k_factor,
            pairing_strategy=pairing,
            early_stop_enabled=early_stop,
            batch_size=elo_concurrency,
            interactive=False,  # No interactive display in Lambda
        )

        ranker = EloRanker(profile, candidates, ranker_config)

        logger.info(f"Starting ELO ranking for {len(candidates)} candidates")
        ranked_candidates = await ranker.rank_candidates()

        # Save ELO results
        elo_path = results_dir / f"elo_ranked_k{int(k_factor)}_p{pairing}.json"
        elo_data = {
            "query": query,
            "total_ranked": len(ranked_candidates),
            "matches_played": len(ranker.match_history),
            "papers": [
                {
                    "paper_id": c.candidate.paper_id,
                    "title": c.candidate.title,
                    "abstract": c.candidate.abstract[:500] if c.candidate.abstract else None,
                    "year": c.candidate.year,
                    "citation_count": c.candidate.citation_count,
                    "elo_rating": round(c.elo, 1),
                    "wins": c.wins,
                    "losses": c.losses,
                    "draws": c.draws,
                }
                for c in ranked_candidates
            ]
        }
        with open(elo_path, "w") as f:
            json.dump(elo_data, f, indent=2)

        events = append_event(events, "phase_complete", "ranking", f"Ranking complete: {len(ranker.match_history)} matches played")
        update_job_progress(
            job_id, JobStatus.RUNNING.value, "ranking", 1,
            f"Ranking complete: {len(ranker.match_history)} matches", events=events
        )

        # =========================================================================
        # PHASE 3: REPORT
        # =========================================================================
        events = append_event(events, "phase_start", "report", "Starting report generation")
        update_job_progress(job_id, JobStatus.RUNNING.value, "report", 0, "Starting report generation...", events=events)

        def report_progress_callback(step, step_name, current, total, message):
            nonlocal events
            events = append_event(events, "progress", "report", message, step=step, step_name=step_name)
            update_job_progress(
                job_id, JobStatus.RUNNING.value, "report", step, message,
                current=current, total=total, events=events
            )

        logger.info(f"Starting report generation with top {report_top_k} papers")
        report = await generate_report(
            snowball_file=snowball_path,
            elo_file=elo_path,
            top_k=report_top_k,
            progress_callback=report_progress_callback,
        )

        # Save report
        report_path = results_dir / f"report_top_k{report_top_k}.json"
        report_dict = report_to_dict(report)
        with open(report_path, "w") as f:
            json.dump(report_dict, f, indent=2)

        events = append_event(events, "phase_complete", "report", "Report generation complete")

        # =========================================================================
        # UPLOAD TO S3
        # =========================================================================
        events = append_event(events, "phase_start", "upload", "Uploading artifacts to S3")
        update_job_progress(job_id, JobStatus.RUNNING.value, "upload", 0, "Uploading to S3...", events=events)

        s3_prefix = f"results/{query_slug}/{job_id}"

        # Create metadata.json
        metadata = {
            "job_id": job_id,
            "query": query,
            "created_at": datetime.now(UTC).isoformat(),
            "files": {
                "snowball": "snowball.json",
                "elo_ranked": elo_path.name,
                "report": report_path.name,
            },
            "stats": {
                "papers_found": len(accepted_papers),
                "papers_ranked": len(ranked_candidates),
                "matches_played": len(ranker.match_history),
                "report_papers": report_top_k,
            }
        }
        metadata_path = results_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        if RESULTS_BUCKET:
            artifacts = upload_artifacts_to_s3(results_dir, RESULTS_BUCKET, s3_prefix)
            events = append_event(events, "phase_complete", "upload", f"Uploaded {len(artifacts)} files to S3")
        else:
            logger.warning("RESULTS_BUCKET not set, skipping S3 upload")
            artifacts = []

        # =========================================================================
        # BUILD RESULT
        # =========================================================================
        result = {
            "papers_found": len(accepted_papers),
            "papers_ranked": len(ranked_candidates),
            "matches_played": len(ranker.match_history),
            "report_sections": len(report.current_research),
            "results_bucket": RESULTS_BUCKET,
            "results_prefix": s3_prefix,
            "artifacts": [a["key"] for a in artifacts],
            # Include top 5 papers in summary for quick access
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
        # Cleanup workspace
        try:
            shutil.rmtree(workspace)
            logger.info(f"Cleaned up workspace: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace: {e}")


def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Process a job based on its type.
    
    Args:
        job_id: Unique job identifier
        job_type: Type of job (search, ranking, clustering, etc.)
        payload: Job-specific parameters
        
    Returns:
        Result dictionary
        
    Raises:
        ValueError: If job_type is unknown
    """
    logger.info(f"Processing job {job_id} of type {job_type}")

    # Initialize events list
    events: list[dict] = []
    events = append_event(events, "job_start", "init", f"Starting {job_type} job")

    # Update status to running
    update_job_progress(job_id, JobStatus.RUNNING.value, "init", 0, "Initializing...", events=events)

    if job_type == "pipeline":
        # Run the full pipeline asynchronously
        result = asyncio.run(run_pipeline(job_id, payload, events))

    elif job_type == "search":
        # Search-only job (not implemented yet)
        result = {"message": "Search-only job not yet implemented", "status": "stub"}

    elif job_type == "ranking":
        result = {"message": "Ranking-only job not yet implemented", "status": "stub"}

    elif job_type == "report":
        result = {"message": "Report-only job not yet implemented", "status": "stub"}

    else:
        raise ValueError(f"Unknown job type: {job_type}")

    return result


def handler(event: dict, context) -> dict:
    """Lambda handler for SQS events.
    
    Processes messages from the SQS queue and returns batch item failures
    for any messages that couldn't be processed.
    """
    logger.info(f"Received {len(event.get('Records', []))} records")

    batch_item_failures = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        job_id = None

        try:
            # Parse the message body
            body = json.loads(record.get("body", "{}"))

            job_id = body.get("job_id")
            job_type = body.get("job_type")
            payload = body.get("payload", {})

            if not job_id or not job_type:
                logger.error("Invalid message format: missing job_id or job_type")
                continue

            # Process the job
            result = process_job(job_id, job_type, payload)

            # Update job as completed
            update_job_progress(
                job_id, JobStatus.COMPLETED.value, "complete", 0,
                "Job completed successfully", result=result
            )

            logger.info(f"Successfully processed job {job_id}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message {message_id}: {e}")
            continue

        except Exception as e:
            logger.exception(f"Failed to process message {message_id}: {e}")

            # Try to update job status to failed
            try:
                if job_id:
                    update_job_progress(
                        job_id, JobStatus.FAILED.value, "error", 0,
                        f"Job failed: {str(e)}", error=str(e)
                    )
            except Exception:
                pass

            # Add to batch failures for retry
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
