"""Ranking API routes."""

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from paperpilot.api.schemas import RankingRequest, RankingResponse
from paperpilot.core.elo_ranker import EloRanker, RankerConfig
from paperpilot.core.elo_ranker.models import CandidateElo
from paperpilot.core.models import EdgeType, SnowballCandidate
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/ranking", tags=["ranking"])

# In-memory job storage
jobs: dict[str, dict] = {}

results_manager = ResultsManager()


class ApiRankingEventHandler:
    """Event handler that updates job state for live ranking updates."""

    def __init__(self, job_id: str, initial_elo: float = 1500.0):
        self.job_id = job_id
        self.initial_elo = initial_elo

    def _candidates_to_papers(self, candidates: list[CandidateElo]) -> list[dict[str, Any]]:
        """Convert CandidateElo objects to paper dicts for API response."""
        # Sort by Elo rating (highest first)
        sorted_candidates = sorted(candidates, key=lambda x: x.elo, reverse=True)

        ranked_papers = []
        for i, ce in enumerate(sorted_candidates, 1):
            ranked_papers.append({
                "rank": i,
                "elo": round(ce.elo, 1),
                "elo_change": round(ce.elo - self.initial_elo, 1),
                "wins": ce.wins,
                "losses": ce.losses,
                "draws": ce.draws,
                "paper_id": ce.candidate.paper_id,
                "title": ce.candidate.title,
                "year": ce.candidate.year,
                "citation_count": ce.candidate.citation_count,
                "abstract": ce.candidate.abstract[:500] if ce.candidate.abstract else None,
            })
        return ranked_papers

    def on_elo_update(
        self,
        candidates: list[CandidateElo],
        match_num: int,
        total_matches: int,
        **kwargs: Any
    ) -> None:
        """Update job state with current rankings."""
        if self.job_id not in jobs:
            return

        # Update job state with current rankings
        jobs[self.job_id]["papers"] = self._candidates_to_papers(candidates)
        jobs[self.job_id]["matches_played"] = match_num
        jobs[self.job_id]["total_matches"] = total_matches

    def on_progress(self, *args: Any, **kwargs: Any) -> None:
        """Handle progress updates."""
        pass

    def on_match_complete(self, *args: Any, **kwargs: Any) -> None:
        """Handle match completion."""
        pass

    def on_match_start(self, *args: Any, **kwargs: Any) -> None:
        """Handle match start."""
        pass

    def on_paper_accepted(self, *args: Any, **kwargs: Any) -> None:
        """Not used in ranking."""
        pass

    def on_paper_rejected(self, *args: Any, **kwargs: Any) -> None:
        """Not used in ranking."""
        pass

    def on_iteration_start(self, *args: Any, **kwargs: Any) -> None:
        """Not used in ranking."""
        pass

    def on_iteration_complete(self, *args: Any, **kwargs: Any) -> None:
        """Not used in ranking."""
        pass

    def on_snowball_stop(self, *args: Any, **kwargs: Any) -> None:
        """Not used in ranking."""
        pass


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
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                papers = data.get("papers", [])
                query = data.get("query", request.query)
        else:
            # Use latest snowball results for query
            snowball_path = results_manager.get_latest_snowball(request.query)
            if snowball_path is None:
                raise FileNotFoundError(f"No snowball results found for query: {request.query}")
            with open(snowball_path, encoding="utf-8") as f:
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

        # Create event handler for live updates
        event_handler = ApiRankingEventHandler(job_id=job_id, initial_elo=config.initial_elo)

        # Initialize job state with progress tracking
        jobs[job_id]["matches_played"] = 0
        jobs[job_id]["total_matches"] = config.max_matches or (len(candidates) * 3)
        jobs[job_id]["papers"] = []  # Will be updated by event handler

        # Create and run Elo ranker with event handler
        ranker = EloRanker(
            profile=profile,
            candidates=candidates,
            config=config,
            event_handler=event_handler,
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
        jobs[job_id]["matches_played"] = len(ranker.match_history)
        jobs[job_id]["total_matches"] = len(ranker.match_history)

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
        "matches_played": 0,
        "total_matches": 0,
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
        matches_played=job.get("matches_played", 0),
        total_matches=job.get("total_matches", 0),
    )
