"""Ranking API routes."""

import json
from typing import Dict
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from paperpilot.api.schemas import RankingRequest, RankingResponse
from paperpilot.core.elo_ranker import EloRanker, RankerConfig
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.models import SnowballCandidate, EdgeType
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/ranking", tags=["ranking"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

results_manager = ResultsManager()


async def _run_ranking_task(job_id: str, request: RankingRequest):
    """Background task to run Elo ranking."""
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
        
        if len(papers) < 2:
            raise ValueError("Need at least 2 papers for Elo ranking")
        
        # Validate pairing strategy
        if request.pairing not in ["random", "swiss"]:
            raise ValueError(f"Invalid pairing strategy: {request.pairing}. Must be 'random' or 'swiss'")
        
        # Generate query profile for relevance judgment
        profile = await generate_query_profile(query)
        
        # Convert papers to SnowballCandidate objects
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
        
        # Create configuration
        config = RankerConfig(
            k_factor=request.k_factor,
            max_matches=request.n_matches,
            pairing_strategy=request.pairing,
            early_stop_enabled=request.early_stop,
            concurrency=request.concurrency,
            tournament_mode=request.tournament,
            interactive=False,  # No interactive display in API
        )
        
        # Create and run Elo ranker (no event handler for API)
        ranker = EloRanker(
            profile=profile,
            candidates=candidates,
            config=config,
            event_handler=None,
        )
        
        ranked = await ranker.rank_candidates()
        
        # Export ranked results
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
            "k_factor": request.k_factor,
            "total_matches": len(ranker.match_history),
            "total_papers": len(ranked),
            "papers": ranked_papers,
        }
        
        # Save using ResultsManager
        saved_path = results_manager.save_elo_ranking(
            query,
            results,
            pairing=request.pairing,
            k_factor=request.k_factor,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["papers"] = ranked_papers
        jobs[job_id]["result_path"] = str(saved_path.relative_to(results_manager.base_dir))
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("", response_model=RankingResponse, status_code=202)
async def start_ranking(
    request: RankingRequest,
    background_tasks: BackgroundTasks
):
    """Start a new Elo ranking job.
    
    Returns immediately with a job_id. Use GET /api/ranking/{job_id} to check status.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "papers": [],
        "result_path": None,
    }
    
    # Run ranking in background
    background_tasks.add_task(_run_ranking_task, job_id, request)
    
    return RankingResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
        papers=[],
        result_path=None,
    )


@router.get("/{job_id}", response_model=RankingResponse)
async def get_ranking_results(job_id: str):
    """Get ranking results by job ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Ranking failed: {error}")
    
    return RankingResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        papers=job["papers"],
        result_path=job.get("result_path"),
    )
