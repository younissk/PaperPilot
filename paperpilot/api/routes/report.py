"""Report API routes."""

import json
from typing import Dict, Callable
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


class ApiReportProgressHandler:
    """Progress handler that updates job state for live report generation updates."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def __call__(self, step: int, step_name: str, current: int, total: int, message: str) -> None:
        """Update job state with current progress."""
        if self.job_id not in jobs:
            return
        
        # Update job state with current progress
        jobs[self.job_id]["current_step"] = step
        jobs[self.job_id]["step_name"] = step_name
        jobs[self.job_id]["current_progress"] = current
        jobs[self.job_id]["total_progress"] = total
        jobs[self.job_id]["progress_message"] = message


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
        
        # Check if report already exists
        query_dir = results_manager.get_query_dir(query)
        if request.top_k is not None:
            report_filename = results_manager._build_filename("report", {"top_k": request.top_k}, "json")
        else:
            report_filename = "report.json"
        existing_report_path = query_dir / report_filename
        
        if existing_report_path.exists():
            # Load existing report
            with open(existing_report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["report_data"] = report_data
            jobs[job_id]["report_path"] = str(existing_report_path.relative_to(results_manager.base_dir))
            jobs[job_id]["current_step"] = 8
            jobs[job_id]["step_name"] = "Completed (loaded from cache)"
            jobs[job_id]["current_progress"] = 1
            jobs[job_id]["total_progress"] = 1
            jobs[job_id]["progress_message"] = "Report loaded from existing file"
            return
        
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
        
        # Create progress handler for live updates
        progress_handler = ApiReportProgressHandler(job_id)
        
        # Initialize job state with progress tracking
        jobs[job_id]["current_step"] = 0
        jobs[job_id]["step_name"] = "Starting..."
        jobs[job_id]["current_progress"] = 0
        jobs[job_id]["total_progress"] = 0
        jobs[job_id]["progress_message"] = "Initializing report generation..."
        
        # Generate report with progress callback
        report_obj = await generate_report(
            snowball_file=snowball_path,
            elo_file=elo_path,
            top_k=request.top_k,
            progress_callback=progress_handler,
        )
        
        # Convert to dict for saving
        report_data = report_to_dict(report_obj)
        
        # Save using ResultsManager (for persistence, but not exposed to frontend)
        output_path = results_manager.save_report(
            query=query,
            report_data=report_data,
            top_k=request.top_k,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["report_data"] = report_data
        # Keep path for backward compatibility but not primary
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
        "report_data": None,
        "report_path": None,
        "current_step": 0,
        "step_name": "",
        "current_progress": 0,
        "total_progress": 0,
        "progress_message": "",
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
        report_data=job.get("report_data"),
        report_path=job.get("report_path"),
        current_step=job.get("current_step", 0),
        step_name=job.get("step_name", ""),
        current_progress=job.get("current_progress", 0),
        total_progress=job.get("total_progress", 0),
        progress_message=job.get("progress_message", ""),
    )
