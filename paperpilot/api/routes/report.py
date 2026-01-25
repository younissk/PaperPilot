"""Report API routes."""

import json
from typing import Dict
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import ReportRequest, ReportResponse
from paperpilot.core.report.generator import generate_report, report_to_dict
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/report", tags=["report"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_report_task(job_id: str, request: ReportRequest):
    """Background task to generate report."""
    try:
        jobs[job_id]["status"] = "running"
        
        # Determine snowball file path
        snowball_path = None
        if request.file_path:
            snowball_path = Path(request.file_path)
            if not snowball_path.exists():
                raise FileNotFoundError(f"File not found: {request.file_path}")
        else:
            # Use latest snowball results for query
            snowball_path = results_manager.get_latest_snowball(request.query)
            if snowball_path is None:
                raise FileNotFoundError(f"No snowball results found for query: {request.query}")
        
        # Load query from file
        with open(snowball_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            query = data.get("query", request.query)
        
        # Determine elo file path
        elo_path = None
        if request.elo_file_path:
            elo_path = Path(request.elo_file_path)
            if not elo_path.exists():
                # Try to find it in query directory
                query_dir = results_manager.get_query_dir(query)
                elo_path = query_dir / request.elo_file_path
                if not elo_path.exists():
                    elo_path = None  # Will auto-detect
        else:
            # Auto-detect elo file in query directory
            query_dir = results_manager.get_query_dir(query)
            elo_candidates = list(query_dir.glob("elo_ranked*.json"))
            if elo_candidates:
                # Use the most recent one
                elo_path = max(elo_candidates, key=lambda p: p.stat().st_mtime)
        
        # Generate report
        report_obj = await generate_report(
            snowball_file=snowball_path,
            elo_file=elo_path,
            top_k=request.top_k,
        )
        
        # Convert to dict for saving
        report_data = report_to_dict(report_obj)
        
        # Save using ResultsManager
        output_path = results_manager.save_report(
            query=query,
            report_data=report_data,
            top_k=request.top_k,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["report_path"] = str(output_path.relative_to(results_manager.base_dir))
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=ReportResponse, status_code=202)
async def start_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Start a new report generation job.
    
    Returns immediately with a job_id. Use GET /api/report/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "report_path": None,
    }
    
    # Run report generation in background
    background_tasks.add_task(_run_report_task, job_id, request)
    
    return ReportResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        report_path=None,
    )


@router.get("/{job_id}", response_model=ReportResponse)
async def get_report_results(job_id: str):
    """Get report results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {error}")
    
    return ReportResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        report_path=job.get("report_path"),
    )
