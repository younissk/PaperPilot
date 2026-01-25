"""Search API routes."""

from typing import Dict
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import SearchRequest, SearchResponse
from paperpilot.core.service import run_search
from paperpilot.core.models import AcceptedPaper
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/search", tags=["search"])

# In-memory job storage (in production, use a database)
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


class ApiSearchProgressHandler:
    """Progress handler that updates job state for live search progress updates."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def __call__(
        self,
        step: int,
        step_name: str,
        current: int = 0,
        total: int = 0,
        message: str = "",
        current_iteration: int = 0,
        total_iterations: int = 0,
    ) -> None:
        """Update job state with current progress.
        
        Args:
            step: Current step number (0-6)
            step_name: Human-readable step name
            current: Current progress value
            total: Total progress value
            message: Descriptive progress message
            current_iteration: Current snowball iteration (0 = initial)
            total_iterations: Maximum iterations configured
        """
        if self.job_id not in jobs:
            return
        
        # Update job state with current progress
        jobs[self.job_id]["current_step"] = step
        jobs[self.job_id]["step_name"] = step_name
        jobs[self.job_id]["current_progress"] = current
        jobs[self.job_id]["total_progress"] = total
        jobs[self.job_id]["progress_message"] = message
        jobs[self.job_id]["current_iteration"] = current_iteration
        jobs[self.job_id]["total_iterations"] = total_iterations


def _paper_to_dict(paper: AcceptedPaper) -> dict:
    """Convert AcceptedPaper to dict for JSON response."""
    return {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "abstract": paper.abstract[:500] if paper.abstract else None,
        "year": paper.year,
        "citation_count": paper.citation_count,
        "discovered_from": paper.discovered_from,
        "edge_type": paper.edge_type.value,
        "depth": paper.depth,
        "judge_reason": paper.judge_reason,
        "judge_confidence": paper.judge_confidence,
    }


async def _run_search_task(job_id: str, request: SearchRequest):
    """Background task to run the search."""
    try:
        jobs[job_id]["status"] = "running"
        
        # Initialize progress fields
        jobs[job_id]["current_step"] = 0
        jobs[job_id]["step_name"] = "Starting search..."
        jobs[job_id]["current_progress"] = 0
        jobs[job_id]["total_progress"] = 0
        jobs[job_id]["progress_message"] = "Initializing search..."
        jobs[job_id]["current_iteration"] = 0
        jobs[job_id]["total_iterations"] = request.max_iterations
        
        # Create progress handler
        progress_handler = ApiSearchProgressHandler(job_id)
        
        # Run search without output file - we'll save using ResultsManager
        papers = await run_search(
            query=request.query,
            num_results=request.num_results,
            output_file="",  # Empty string means don't save (we'll do it manually)
            max_iterations=request.max_iterations,
            max_accepted=request.max_accepted,
            top_n=request.top_n,
            progress_callback=progress_handler,
        )
        
        # Save using ResultsManager
        saved_path = results_manager.save_snowball(request.query, {
            "query": request.query,
            "total_accepted": len(papers),
            "papers": [_paper_to_dict(p) for p in papers],
        })
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["total_accepted"] = len(papers)
        jobs[job_id]["papers"] = [_paper_to_dict(p) for p in papers]
        jobs[job_id]["result_path"] = str(saved_path.relative_to(results_manager.base_dir))
        jobs[job_id]["current_step"] = 6
        jobs[job_id]["step_name"] = "Completed"
        jobs[job_id]["progress_message"] = f"Search completed! Found {len(papers)} papers."
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["progress_message"] = f"Search failed: {str(e)}"


@router.post("", response_model=SearchResponse, status_code=202)
async def start_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks
):
    """Start a new search job.
    
    Returns immediately with a job_id. Use GET /api/search/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "total_accepted": 0,
        "papers": [],
        "current_step": 0,
        "step_name": "Queued",
        "current_progress": 0,
        "total_progress": 0,
        "progress_message": "Waiting to start...",
        "current_iteration": 0,
        "total_iterations": request.max_iterations,
    }
    
    # Run search in background
    background_tasks.add_task(_run_search_task, job_id, request)
    
    return SearchResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        total_accepted=0,
        papers=[],
        result_path=None,
    )


@router.get("/{job_id}", response_model=SearchResponse)
async def get_search_results(job_id: str):
    """Get search results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Search failed: {error}")
    
    return SearchResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        total_accepted=job["total_accepted"],
        papers=job["papers"],
        result_path=job.get("result_path"),
        current_step=job.get("current_step", 0),
        step_name=job.get("step_name", ""),
        current_progress=job.get("current_progress", 0),
        total_progress=job.get("total_progress", 0),
        progress_message=job.get("progress_message", ""),
        current_iteration=job.get("current_iteration", 0),
        total_iterations=job.get("total_iterations", 0),
    )
