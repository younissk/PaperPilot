"""Pipeline API routes - unified search + ELO ranking + report generation."""

import json
import asyncio
from typing import Dict, List, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from paperpilot.api.schemas import PipelineRequest, PipelineResponse
from paperpilot.core.service import run_search
from paperpilot.core.models import AcceptedPaper
from paperpilot.core.elo_ranker import EloRanker, RankerConfig
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.models import SnowballCandidate
from paperpilot.core.report.generator import generate_report, report_to_dict
from paperpilot.core.results import ResultsManager
from paperpilot.core.elo_ranker.models import CandidateElo

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# In-memory job storage
jobs: Dict[str, Dict] = {}

# SSE event queues for each job
sse_queues: Dict[str, asyncio.Queue] = {}

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


def _emit_sse_event(job_id: str, event_type: str, data: Dict[str, Any]):
    """Emit an SSE event to the queue (thread-safe, can be called from sync code)."""
    if job_id in sse_queues:
        try:
            event_data = json.dumps(data)
            sse_queues[job_id].put_nowait(f"event: {event_type}\ndata: {event_data}\n\n")
        except asyncio.QueueFull:
            # Queue is full, skip this event (shouldn't happen in practice)
            pass


class PipelineSearchProgressHandler:
    """Progress handler for search phase."""
    
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
        """Update job state and emit SSE event."""
        if self.job_id not in jobs:
            return
        
        # Update job state
        jobs[self.job_id]["phase"] = "search"
        jobs[self.job_id]["phase_step"] = step
        jobs[self.job_id]["phase_step_name"] = step_name
        jobs[self.job_id]["phase_progress"] = current
        jobs[self.job_id]["phase_total"] = total
        jobs[self.job_id]["progress_message"] = message
        
        # Emit SSE event
        _emit_sse_event(self.job_id, "progress", {
            "phase": "search",
            "step": step,
            "step_name": step_name,
            "current": current,
            "total": total,
            "message": message,
            "current_iteration": current_iteration,
            "total_iterations": total_iterations,
        })


class PipelineRankingEventHandler:
    """Event handler for ELO ranking phase."""
    
    def __init__(self, job_id: str, initial_elo: float = 1500.0):
        self.job_id = job_id
        self.initial_elo = initial_elo
        self.match_history: List[Dict[str, Any]] = []
        self.current_match: Optional[Dict[str, Any]] = None
    
    def _candidates_to_papers(self, candidates: List[CandidateElo]) -> List[Dict[str, Any]]:
        """Convert CandidateElo objects to paper dicts."""
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
    
    def _calculate_match_stats(self) -> Dict[str, Any]:
        """Calculate match statistics from match history."""
        if not self.match_history:
            return {
                "total_completed": 0,
                "p1_wins": 0,
                "p2_wins": 0,
                "draws": 0,
            }
        
        wins_p1 = sum(1 for m in self.match_history if m.get("winner") == 1)
        wins_p2 = sum(1 for m in self.match_history if m.get("winner") == 2)
        draws = sum(1 for m in self.match_history if m.get("winner") is None)
        
        return {
            "total_completed": len(self.match_history),
            "p1_wins": wins_p1,
            "p2_wins": wins_p2,
            "draws": draws,
        }
    
    def on_elo_update(
        self,
        candidates: List[CandidateElo],
        match_num: int,
        total_matches: int,
        **kwargs: Any
    ) -> None:
        """Update job state and emit SSE event."""
        if self.job_id not in jobs:
            return
        
        ranked_papers = self._candidates_to_papers(candidates)
        jobs[self.job_id]["papers"] = ranked_papers
        
        # Calculate match statistics
        match_stats = self._calculate_match_stats()
        
        # Emit SSE event with full details
        _emit_sse_event(self.job_id, "progress", {
            "phase": "ranking",
            "step": 0,
            "step_name": "Running ELO matches",
            "current": match_num,
            "total": total_matches,
            "message": f"Match {match_num} of {total_matches}",
            "papers": ranked_papers,  # Full ranked papers list
            "match_stats": match_stats,
            "current_match": self.current_match,
            "last_match": self.match_history[-1] if self.match_history else None,
        })
    
    def on_match_complete(self, match: Any, **kwargs: Any) -> None:
        """Handle match completion."""
        # Convert MatchResult to dict
        match_dict = {
            "paper1_title": match.paper1_title,
            "paper2_title": match.paper2_title,
            "winner": match.winner,
            "reason": match.reason,
        }
        self.match_history.append(match_dict)
        self.current_match = None
    
    def on_match_start(
        self,
        paper1_title: str,
        paper2_title: str,
        **kwargs: Any
    ) -> None:
        """Handle match start."""
        self.current_match = {
            "paper1_title": paper1_title,
            "paper2_title": paper2_title,
            "winner": None,
            "reason": "",
        }
    
    def on_progress(self, *args: Any, **kwargs: Any) -> None:
        """Handle progress updates."""
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


class PipelineReportProgressHandler:
    """Progress handler for report generation phase."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def __call__(self, step: int, step_name: str, current: int, total: int, message: str) -> None:
        """Update job state and emit SSE event."""
        if self.job_id not in jobs:
            return
        
        # Update job state
        jobs[self.job_id]["phase"] = "report"
        jobs[self.job_id]["phase_step"] = step
        jobs[self.job_id]["phase_step_name"] = step_name
        jobs[self.job_id]["phase_progress"] = current
        jobs[self.job_id]["phase_total"] = total
        jobs[self.job_id]["progress_message"] = message
        
        # Emit SSE event
        _emit_sse_event(self.job_id, "progress", {
            "phase": "report",
            "step": step,
            "step_name": step_name,
            "current": current,
            "total": total,
            "message": message,
        })


async def _run_pipeline_task(job_id: str, request: PipelineRequest):
    """Background task to run the full pipeline."""
    try:
        # Phase 1: Search
        jobs[job_id]["status"] = "searching"
        _emit_sse_event(job_id, "phase_start", {"phase": "search"})
        
        search_progress = PipelineSearchProgressHandler(job_id)
        
        papers = await run_search(
            query=request.query,
            num_results=request.num_results,
            output_file="",
            max_iterations=request.max_iterations,
            max_accepted=request.max_accepted,
            top_n=request.top_n,
            progress_callback=search_progress,
        )
        
        # Save search results
        saved_path = results_manager.save_snowball(request.query, {
            "query": request.query,
            "total_accepted": len(papers),
            "papers": [_paper_to_dict(p) for p in papers],
        })
        
        jobs[job_id]["papers"] = [_paper_to_dict(p) for p in papers]
        _emit_sse_event(job_id, "phase_complete", {
            "phase": "search",
            "papers_found": len(papers),
            "result_path": str(saved_path.relative_to(results_manager.base_dir)),
        })
        
        if len(papers) < 2:
            raise ValueError("Need at least 2 papers for ELO ranking")
        
        # Phase 2: ELO Ranking
        jobs[job_id]["status"] = "ranking"
        _emit_sse_event(job_id, "phase_start", {"phase": "ranking"})
        
        # Generate query profile
        profile = await generate_query_profile(request.query)
        
        # Store query profile in job state (convert to dict for JSON serialization)
        jobs[job_id]["query_profile"] = {
            "core_query": profile.core_query,
            "domain_description": profile.domain_description,
            "required_concepts": profile.required_concepts,
            "required_concept_groups": profile.required_concept_groups,
            "optional_concepts": profile.optional_concepts,
            "exclusion_concepts": profile.exclusion_concepts,
            "keyword_patterns": profile.keyword_patterns,
            "domain_boundaries": profile.domain_boundaries,
            "fallback_queries": profile.fallback_queries,
        }
        
        # Emit query profile in SSE event
        _emit_sse_event(job_id, "query_profile", {
            "query_profile": jobs[job_id]["query_profile"],
        })
        
        # Convert papers to SnowballCandidate objects
        candidates = []
        for p in papers:
            candidate = SnowballCandidate(
                paper_id=p.paper_id,
                title=p.title,
                abstract=p.abstract,
                year=p.year,
                citation_count=p.citation_count,
                influential_citation_count=0,
                discovered_from=p.discovered_from,
                edge_type=p.edge_type,
                depth=p.depth,
            )
            candidates.append(candidate)
        
        # Create ranking configuration
        config = RankerConfig(
            k_factor=request.k_factor,
            max_matches=len(candidates) * 3,  # Default: 3 matches per paper
            pairing_strategy=request.pairing,
            early_stop_enabled=request.early_stop,
            concurrency=request.elo_concurrency,
            tournament_mode=False,
            interactive=False,
        )
        
        # Create event handler
        ranking_handler = PipelineRankingEventHandler(job_id=job_id, initial_elo=config.initial_elo)
        
        # Run ranking
        ranker = EloRanker(
            profile=profile,
            candidates=candidates,
            config=config,
            event_handler=ranking_handler,
        )
        
        ranked = await ranker.rank_candidates()
        
        # Convert to ranked papers
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
        
        # Save ranking results
        ranking_results = {
            "query": request.query,
            "ranking_method": "elo",
            "k_factor": request.k_factor,
            "total_matches": len(ranker.match_history),
            "total_papers": len(ranked),
            "papers": ranked_papers,
        }
        
        elo_saved_path = results_manager.save_elo_ranking(
            request.query,
            ranking_results,
            pairing=request.pairing,
            k_factor=request.k_factor,
        )
        
        jobs[job_id]["papers"] = ranked_papers
        _emit_sse_event(job_id, "phase_complete", {
            "phase": "ranking",
            "papers_ranked": len(ranked_papers),
            "result_path": str(elo_saved_path.relative_to(results_manager.base_dir)),
        })
        
        # Phase 3: Report Generation
        jobs[job_id]["status"] = "reporting"
        _emit_sse_event(job_id, "phase_start", {"phase": "report"})
        
        report_progress = PipelineReportProgressHandler(job_id)
        
        # Generate report using the ELO-ranked file
        report_obj = await generate_report(
            snowball_file=saved_path,
            elo_file=elo_saved_path,
            top_k=request.report_top_k,
            progress_callback=report_progress,
        )
        
        # Convert to dict
        report_data = report_to_dict(report_obj)
        
        # Save report
        report_saved_path = results_manager.save_report(
            query=request.query,
            report_data=report_data,
            top_k=request.report_top_k,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["report_data"] = report_data
        _emit_sse_event(job_id, "phase_complete", {
            "phase": "report",
            "result_path": str(report_saved_path.relative_to(results_manager.base_dir)),
        })
        
        # Final completion event
        _emit_sse_event(job_id, "complete", {
            "papers": ranked_papers,
            "report_data": report_data,
        })
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        _emit_sse_event(job_id, "error", {
            "error": str(e),
            "phase": jobs[job_id].get("phase", "unknown"),
        })


async def _sse_stream_generator(job_id: str):
    """Generator for SSE stream."""
    try:
        while True:
            # Check if job is complete or failed
            if job_id in jobs:
                status = jobs[job_id].get("status")
                if status in ["completed", "failed"]:
                    # Send final event and break
                    if status == "completed":
                        yield f"event: complete\ndata: {json.dumps({'papers': jobs[job_id].get('papers', []), 'report_data': jobs[job_id].get('report_data')})}\n\n"
                    else:
                        error = jobs[job_id].get("error", "Unknown error")
                        yield f"event: error\ndata: {json.dumps({'error': error})}\n\n"
                    break
            
            # Get event from queue (with timeout)
            try:
                event = await asyncio.wait_for(sse_queues[job_id].get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"
                continue
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        # Cleanup
        if job_id in sse_queues:
            del sse_queues[job_id]


@router.post("", response_model=PipelineResponse, status_code=202)
async def start_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """Start a new pipeline job (search + ELO ranking + report).
    
    Returns immediately with a job_id. Use GET /api/pipeline/{job_id}/stream for SSE updates.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "query": request.query,
        "phase": "",
        "phase_step": 0,
        "phase_step_name": "",
        "phase_progress": 0,
        "phase_total": 0,
        "progress_message": "Waiting to start...",
        "papers": [],
        "report_data": None,
    }
    
    # Create SSE queue for this job
    sse_queues[job_id] = asyncio.Queue()
    
    # Run pipeline in background
    background_tasks.add_task(_run_pipeline_task, job_id, request)
    
    return PipelineResponse(
        job_id=job_id,
        status="queued",
        query=request.query,
    )


@router.get("/{job_id}", response_model=PipelineResponse)
async def get_pipeline_status(job_id: str):
    """Get pipeline status by job ID (polling fallback)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "failed":
        error = job.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {error}")
    
    return PipelineResponse(
        job_id=job_id,
        status=job["status"],
        query=job["query"],
        phase=job.get("phase", ""),
        phase_step=job.get("phase_step", 0),
        phase_step_name=job.get("phase_step_name", ""),
        phase_progress=job.get("phase_progress", 0),
        phase_total=job.get("phase_total", 0),
        progress_message=job.get("progress_message", ""),
        papers=job.get("papers", []),
        report_data=job.get("report_data"),
        query_profile=job.get("query_profile"),
    )


@router.get("/{job_id}/stream")
async def stream_pipeline_progress(job_id: str):
    """Stream pipeline progress via Server-Sent Events (SSE)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Ensure queue exists
    if job_id not in sse_queues:
        sse_queues[job_id] = asyncio.Queue()
    
    return StreamingResponse(
        _sse_stream_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
