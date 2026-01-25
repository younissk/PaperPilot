"""Clustering API routes."""

import json
import os
import tempfile
from typing import Dict
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import ClusteringRequest, ClusteringResponse
from paperpilot.core.cluster import ClusteringEngine, ClusteringResult
from paperpilot.core.visualize import save_cluster_visualization
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/clustering", tags=["clustering"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_clustering_task(job_id: str, request: ClusteringRequest):
    """Background task to run clustering."""
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
        
        if len(papers) < 3:
            raise ValueError("Need at least 3 papers for clustering")
        
        # Validate options
        if request.method not in ["hdbscan", "dbscan", "kmeans"]:
            raise ValueError(f"Invalid clustering method: {request.method}. Use 'hdbscan', 'dbscan', or 'kmeans'")
        
        if request.dim_method not in ["umap", "tsne", "pca"]:
            raise ValueError(f"Invalid dimension reduction method: {request.dim_method}. Use 'umap', 'tsne', or 'pca'")
        
        if request.method == "kmeans" and request.n_clusters is None:
            raise ValueError("n_clusters is required for kmeans method")
        
        engine = ClusteringEngine()
        
        # Check feature availability and adjust methods if needed
        features = engine.get_available_features()
        cluster_method = request.method
        dim_method = request.dim_method
        
        if dim_method == "umap" and not features["umap"]:
            dim_method = "pca"
        if cluster_method == "hdbscan" and not features["hdbscan"]:
            cluster_method = "dbscan"
        
        # Step 1: Embed papers
        embeddings = engine.embed_papers(papers)
        
        # Step 2: Reduce dimensions
        coords_2d = engine.reduce_dimensions(embeddings, method=dim_method)
        
        # Step 3: Cluster
        labels = engine.cluster(
            embeddings,
            method=cluster_method,
            n_clusters=request.n_clusters,
            eps=request.eps,
            min_samples=request.min_samples,
        )
        
        # Get summaries
        summaries = engine.get_cluster_summaries(papers, labels)
        actual_clusters = len([s for s in summaries if s.cluster_id != -1])
        
        # Build clustering result for export
        result = ClusteringResult(
            method=cluster_method,
            dim_reduction=dim_method,
            n_clusters=actual_clusters,
            labels=labels,
            coords_2d=coords_2d,
            cluster_summaries=summaries,
            papers=papers,
        )
        
        # Export JSON
        json_data = engine.to_json(result)
        json_data["query"] = query
        
        # Generate HTML content to string by saving to temp file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        save_cluster_visualization(result, tmp_html, title=f"Paper Clusters: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        os.unlink(tmp_html)
        
        # Save using ResultsManager
        json_path, html_path = results_manager.save_clusters(
            query,
            json_data,
            html_content,
            method=cluster_method,
            dim_reduction=dim_method,
            n_clusters=request.n_clusters if cluster_method == "kmeans" else None,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["clusters_json_path"] = str(json_path.relative_to(results_manager.base_dir))
        jobs[job_id]["clusters_html_path"] = str(html_path.relative_to(results_manager.base_dir)) if html_path else None
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=ClusteringResponse, status_code=202)
async def start_clustering(
    request: ClusteringRequest,
    background_tasks: BackgroundTasks
):
    """Start a new clustering job.
    
    Returns immediately with a job_id. Use GET /api/clustering/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "clusters_json_path": None,
        "clusters_html_path": None,
    }
    
    # Run clustering in background
    background_tasks.add_task(_run_clustering_task, job_id, request)
    
    return ClusteringResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        clusters_json_path=None,
        clusters_html_path=None,
    )


@router.get("/{job_id}", response_model=ClusteringResponse)
async def get_clustering_results(job_id: str):
    """Get clustering results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Clustering failed: {error}")
    
    return ClusteringResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        clusters_json_path=job.get("clusters_json_path"),
        clusters_html_path=job.get("clusters_html_path"),
    )
