"""Graph API routes."""

import json
import os
import tempfile
from typing import Dict
import uuid
from pathlib import Path

import aiohttp
from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import GraphRequest, GraphResponse
from paperpilot.core.graph import build_citation_graph
from paperpilot.core.visualize import save_graph_visualization
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/graph", tags=["graph"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_graph_task(job_id: str, request: GraphRequest):
    """Background task to build citation graph."""
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
        
        # Validate direction
        if request.direction not in ["both", "citations", "references"]:
            raise ValueError(f"Invalid direction: {request.direction}. Use 'both', 'citations', or 'references'")
        
        # Build graph
        async with aiohttp.ClientSession() as session:
            graph_data = await build_citation_graph(
                session,
                papers,
                query=query,
                direction=request.direction,
                limit=request.limit,
            )
        
        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        save_graph_visualization(graph_data, tmp_html, title=f"Citation Graph: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        os.unlink(tmp_html)
        
        # Save using ResultsManager
        json_path, html_path = results_manager.save_graph(
            query,
            graph_data,
            html_content,
            direction=request.direction,
            limit=request.limit,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["graph_json_path"] = str(json_path.relative_to(results_manager.base_dir))
        jobs[job_id]["graph_html_path"] = str(html_path.relative_to(results_manager.base_dir)) if html_path else None
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=GraphResponse, status_code=202)
async def start_graph(
    request: GraphRequest,
    background_tasks: BackgroundTasks
):
    """Start a new citation graph building job.
    
    Returns immediately with a job_id. Use GET /api/graph/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "graph_json_path": None,
        "graph_html_path": None,
    }
    
    # Run graph building in background
    background_tasks.add_task(_run_graph_task, job_id, request)
    
    return GraphResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        graph_json_path=None,
        graph_html_path=None,
    )


@router.get("/{job_id}", response_model=GraphResponse)
async def get_graph_results(job_id: str):
    """Get graph results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Graph building failed: {error}")
    
    return GraphResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        graph_json_path=job.get("graph_json_path"),
        graph_html_path=job.get("graph_html_path"),
    )
