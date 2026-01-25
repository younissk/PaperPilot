"""Everything API routes - runs all analysis features."""

import json
import os
import tempfile
from typing import Dict, List
import uuid
from pathlib import Path

import aiohttp
from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import EverythingRequest, EverythingResponse
from paperpilot.core.elo_ranker import EloRanker, RankerConfig
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.models import SnowballCandidate, EdgeType
from paperpilot.core.cluster import ClusteringEngine, ClusteringResult
from paperpilot.core.timeline import create_timeline
from paperpilot.core.graph import build_citation_graph
from paperpilot.core.visualize import (
    save_cluster_visualization,
    save_timeline_visualization,
    save_graph_visualization,
)
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/everything", tags=["everything"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_everything_task(job_id: str, request: EverythingRequest):
    """Background task to run all analysis features."""
    generated_files: List[str] = []
    
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
        
        # 1. Elo Ranking
        try:
            profile = await generate_query_profile(query)
            
            candidates = []
            for p in papers:
                candidate = SnowballCandidate(
                    paper_id=p.get("paper_id", ""),
                    title=p.get("title", "Unknown"),
                    abstract=p.get("abstract"),
                    year=p.get("year"),
                    citation_count=p.get("citation_count", 0),
                    influential_citation_count=0,
                    discovered_from=p.get("discovered_from"),
                    edge_type=EdgeType(p.get("edge_type", "seed")),
                    depth=p.get("depth", 0),
                )
                candidates.append(candidate)
            
            config = RankerConfig(
                k_factor=32.0,
                max_matches=None,
                pairing_strategy="swiss",
                early_stop_enabled=True,
                concurrency=5,
                tournament_mode=False,
                interactive=False,
            )
            
            ranker = EloRanker(
                profile=profile,
                candidates=candidates,
                config=config,
                event_handler=None,
            )
            
            ranked = await ranker.rank_candidates()
            
            ranked_papers = []
            for i, ce in enumerate(ranked, 1):
                ranked_papers.append({
                    "rank": i,
                    "elo": round(ce.elo, 1),
                    "elo_change": round(ce.elo - 1500, 1),
                    "wins": ce.wins,
                    "losses": ce.losses,
                    "draws": ce.draws,
                    "paper_id": ce.candidate.paper_id,
                    "title": ce.candidate.title,
                    "year": ce.candidate.year,
                    "citation_count": ce.candidate.citation_count,
                    "abstract": ce.candidate.abstract[:500] if ce.candidate.abstract else None,
                })
            
            results = {
                "query": query,
                "ranking_method": "elo",
                "k_factor": 32.0,
                "total_matches": len(ranker.match_history),
                "total_papers": len(ranked),
                "papers": ranked_papers,
            }
            
            saved_path = results_manager.save_elo_ranking(
                query,
                results,
                pairing="swiss",
                k_factor=32.0,
            )
            generated_files.append(str(saved_path.relative_to(results_manager.base_dir)))
        except Exception:
            # Continue with other features even if ranking fails
            pass
        
        # 2. Clustering
        try:
            engine = ClusteringEngine()
            features = engine.get_available_features()
            
            cluster_method = "hdbscan"
            dim_method = "umap"
            
            if dim_method == "umap" and not features["umap"]:
                dim_method = "pca"
            if cluster_method == "hdbscan" and not features["hdbscan"]:
                cluster_method = "dbscan"
            
            embeddings = engine.embed_papers(papers)
            coords_2d = engine.reduce_dimensions(embeddings, method=dim_method)
            labels = engine.cluster(
                embeddings,
                method=cluster_method,
                n_clusters=None,
                eps=None,
                min_samples=None,
            )
            
            summaries = engine.get_cluster_summaries(papers, labels)
            actual_clusters = len([s for s in summaries if s.cluster_id != -1])
            
            result = ClusteringResult(
                method=cluster_method,
                dim_reduction=dim_method,
                n_clusters=actual_clusters,
                labels=labels,
                coords_2d=coords_2d,
                cluster_summaries=summaries,
                papers=papers,
            )
            
            json_data = engine.to_json(result)
            json_data["query"] = query
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp_html = tmp.name
            
            save_cluster_visualization(result, tmp_html, title=f"Paper Clusters: {query}")
            
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            os.unlink(tmp_html)
            
            json_path, html_path = results_manager.save_clusters(
                query,
                json_data,
                html_content,
                method=cluster_method,
                dim_reduction=dim_method,
                n_clusters=None,
            )
            generated_files.append(str(json_path.relative_to(results_manager.base_dir)))
            if html_path:
                generated_files.append(str(html_path.relative_to(results_manager.base_dir)))
        except Exception:
            # Continue with other features even if clustering fails
            pass
        
        # 3. Timeline
        try:
            timeline_data = create_timeline(papers, query)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp_html = tmp.name
            
            save_timeline_visualization(timeline_data, tmp_html, title=f"Paper Timeline: {query}")
            
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            os.unlink(tmp_html)
            
            json_path, html_path = results_manager.save_timeline(
                query,
                timeline_data,
                html_content,
            )
            generated_files.append(str(json_path.relative_to(results_manager.base_dir)))
            if html_path:
                generated_files.append(str(html_path.relative_to(results_manager.base_dir)))
        except Exception:
            # Continue with other features even if timeline fails
            pass
        
        # 4. Source Graph
        try:
            async with aiohttp.ClientSession() as session:
                graph_data = await build_citation_graph(
                    session,
                    papers,
                    query=query,
                    direction="both",
                    limit=100,
                )
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp_html = tmp.name
            
            save_graph_visualization(graph_data, tmp_html, title=f"Citation Graph: {query}")
            
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            os.unlink(tmp_html)
            
            json_path, html_path = results_manager.save_graph(
                query,
                graph_data,
                html_content,
                direction="both",
                limit=100,
            )
            generated_files.append(str(json_path.relative_to(results_manager.base_dir)))
            if html_path:
                generated_files.append(str(html_path.relative_to(results_manager.base_dir)))
        except Exception:
            # Continue even if graph fails
            pass
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["generated_files"] = generated_files
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=EverythingResponse, status_code=202)
async def start_everything(
    request: EverythingRequest,
    background_tasks: BackgroundTasks
):
    """Start a new 'everything' job that runs all analysis features.
    
    Returns immediately with a job_id. Use GET /api/everything/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "generated_files": [],
    }
    
    # Run everything in background
    background_tasks.add_task(_run_everything_task, job_id, request)
    
    return EverythingResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        generated_files=[],
    )


@router.get("/{job_id}", response_model=EverythingResponse)
async def get_everything_results(job_id: str):
    """Get everything results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Everything mode failed: {error}")
    
    return EverythingResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        generated_files=job.get("generated_files", []),
    )
