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
        
        # Run search without output file - we'll save using ResultsManager
        papers = await run_search(
            query=request.query,
            num_results=request.num_results,
            output_file="",  # Empty string means don't save (we'll do it manually)
            max_iterations=request.max_iterations,
            max_accepted=request.max_accepted,
            top_n=request.top_n,
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
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


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
    )
