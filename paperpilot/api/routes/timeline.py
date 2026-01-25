"""Timeline API routes."""

import json
import os
import tempfile
from typing import Dict
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import TimelineRequest, TimelineResponse
from paperpilot.core.timeline import create_timeline
from paperpilot.core.visualize import save_timeline_visualization
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_timeline_task(job_id: str, request: TimelineRequest):
    """Background task to create timeline."""
    try:
        jobs[job_id]["status"] = "running"
        
        # Load papers from file or use query
        papers = []
        if request.file_path:
            file_path = Path(request.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {request.file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                papers = data.get("papers", [])
                query = data.get("query", request.query)
        else:
            # Use latest snowball results for query
            snowball_path = results_manager.get_latest_snowball(request.query)
            if snowball_path is None:
                raise FileNotFoundError(f"No snowball results found for query: {request.query}")
            with open(snowball_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                papers = data.get("papers", [])
                query = data.get("query", request.query)
        
        if not papers:
            raise ValueError("No papers found in results file")
        
        # Check if timeline already exists
        query_dir = results_manager.get_query_dir(query)
        existing_json_path = query_dir / "timeline.json"
        existing_html_path = query_dir / "timeline.html"
        
        if existing_json_path.exists():
            # Load existing timeline
            with open(existing_json_path, "r", encoding="utf-8") as f:
                timeline_data = json.load(f)
            
            html_content = None
            if existing_html_path.exists():
                with open(existing_html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["timeline_data"] = timeline_data
            jobs[job_id]["html_content"] = html_content
            jobs[job_id]["timeline_json_path"] = str(existing_json_path.relative_to(results_manager.base_dir))
            jobs[job_id]["timeline_html_path"] = str(existing_html_path.relative_to(results_manager.base_dir)) if html_content else None
            return
        
        # Create timeline data
        timeline_data = create_timeline(papers, query)
        
        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        save_timeline_visualization(timeline_data, tmp_html, title=f"Paper Timeline: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        os.unlink(tmp_html)
        
        # Save using ResultsManager (for persistence, but not exposed to frontend)
        json_path, html_path = results_manager.save_timeline(
            query,
            timeline_data,
            html_content,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["timeline_data"] = timeline_data
        jobs[job_id]["html_content"] = html_content
        # Keep paths for backward compatibility but not primary
        jobs[job_id]["timeline_json_path"] = str(json_path.relative_to(results_manager.base_dir))
        jobs[job_id]["timeline_html_path"] = str(html_path.relative_to(results_manager.base_dir)) if html_path else None
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=TimelineResponse, status_code=202)
async def start_timeline(
    request: TimelineRequest,
    background_tasks: BackgroundTasks
):
    """Start a new timeline creation job.
    
    Returns immediately with a job_id. Use GET /api/timeline/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "timeline_data": None,
        "html_content": None,
        "timeline_json_path": None,
        "timeline_html_path": None,
    }
    
    # Run timeline creation in background
    background_tasks.add_task(_run_timeline_task, job_id, request)
    
    return TimelineResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        timeline_json_path=None,
        timeline_html_path=None,
    )


@router.get("/{job_id}", response_model=TimelineResponse)
async def get_timeline_results(job_id: str):
    """Get timeline results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Timeline creation failed: {error}")
    
    return TimelineResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        timeline_data=job.get("timeline_data"),
        html_content=job.get("html_content"),
        timeline_json_path=job.get("timeline_json_path"),
        timeline_html_path=job.get("timeline_html_path"),
    )
