"""Core service layer for PaperPilot search workflow.

This module provides the main search service without any presentation
dependencies (no Rich, no console output). It returns data structures
that can be used by CLI, API, or other interfaces.
"""

import asyncio
import json
from typing import List

import aiohttp

from paperpilot.core.augment import augment_search
from paperpilot.core.search import search_all_queries
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.models import (
    ReducedArxivEntry,
    SnowballCandidate,
    EdgeType,
    AcceptedPaper,
)
from paperpilot.core.filter import filter_results
from paperpilot.core.openalex import (
    resolve_arxiv_to_openalex,
    get_work_details,
    resolve_by_title,
    extract_openalex_id,
    extract_arxiv_id,
)
from paperpilot.core.snowball import SnowballEngine


async def run_search(
    query: str,
    num_results: int = 5,
    output_file: str = "snowball_results.json",
    max_iterations: int = 5,
    max_accepted: int = 200,
    top_n: int = 50,
) -> List[AcceptedPaper]:
    """Run the full PaperPilot search workflow (async version).
    
    Args:
        query: Research topic to search for
        num_results: Number of results per query variant
        output_file: Output file for results
        max_iterations: Maximum snowball iterations
        max_accepted: Maximum total papers to accept
        top_n: Top N candidates to judge per iteration
        
    Returns:
        List of accepted papers
    """
    # Create shared aiohttp session for all HTTP requests
    async with aiohttp.ClientSession() as session:
        # Step 1: Generate query profile
        profile = await generate_query_profile(query)
        
        # Step 2: Augment the search query
        augmented_queries, _ = await augment_search(query)
        
        # Step 3: Search arXiv for all query variants CONCURRENTLY
        feeds = await search_all_queries(session, augmented_queries, num_results)
        
        # Collect all results
        all_results: List[ReducedArxivEntry] = []
        
        for search_query, feed in zip(augmented_queries, feeds):
            for entry in feed.entries:
                html_link = next(
                    (link.href for link in entry.links if link.type == "text/html"), None
                )
                pdf_link = next(
                    (link.href for link in entry.links if link.type == "application/pdf"), None
                )
                
                all_results.append(ReducedArxivEntry(
                    title=entry.title,
                    updated=entry.updated,
                    summary=entry.summary,
                    link=html_link or pdf_link,
                    source_query=search_query,
                ))
        
        # Step 4: Filter results for relevance (CONCURRENT LLM calls)
        filtered_results, _, _ = await filter_results(profile, all_results)
        
        if not filtered_results:
            return []
        
        # Step 5: Resolve arXiv papers to OpenAlex IDs (CONCURRENT)
        seeds = await _resolve_papers_to_openalex(session, filtered_results)
        
        if not seeds:
            return []
        
        # Step 6: Run the Snowball Engine
        engine = SnowballEngine(
            profile=profile,
            max_iterations=max_iterations,
            top_n_per_iteration=top_n,
            min_new_papers_threshold=3,
            max_total_accepted=max_accepted,
        )
        
        accepted_papers = await engine.run(session, seeds)
        
        # Step 7: Export results
        export_results(accepted_papers, query, output_file)
        
        return accepted_papers


async def _resolve_papers_to_openalex(
    session: aiohttp.ClientSession,
    filtered_results: List[ReducedArxivEntry]
) -> List[SnowballCandidate]:
    """Resolve arXiv papers to OpenAlex IDs concurrently.
    
    Args:
        session: aiohttp ClientSession
        filtered_results: List of filtered arXiv entries
        
    Returns:
        List of SnowballCandidate objects (successfully resolved papers)
    """
    
    async def resolve_single_paper(result: ReducedArxivEntry) -> tuple[ReducedArxivEntry, SnowballCandidate | None]:
        """Resolve a single paper, returning (result, candidate or None)."""
        # Try to resolve via arXiv DOI first
        openalex_id = await resolve_arxiv_to_openalex(session, result.link) if result.link else None
        
        # Fallback: search by title
        if not openalex_id:
            paper_data = await resolve_by_title(session, result.title)
            if paper_data:
                openalex_id = extract_openalex_id(paper_data)
        
        if openalex_id:
            details = await get_work_details(session, openalex_id)
            arxiv_id = extract_arxiv_id(result.link) if result.link else None
            
            seed = SnowballCandidate(
                paper_id=openalex_id,
                title=result.title,
                abstract=result.summary,
                year=details.get("publication_year") if details else None,
                citation_count=details.get("cited_by_count", 0) if details else 0,
                influential_citation_count=0,
                discovered_from=result.source_query,
                edge_type=EdgeType.SEED,
                depth=0,
                arxiv_id=arxiv_id,
            )
            return result, seed
        
        return result, None
    
    # Resolve all papers concurrently
    tasks = [resolve_single_paper(result) for result in filtered_results]
    results = await asyncio.gather(*tasks)
    
    # Collect seeds
    seeds: List[SnowballCandidate] = []
    
    for result, seed in results:
        if seed:
            seeds.append(seed)
    
    return seeds


def export_results(papers: List[AcceptedPaper], query: str, output_file: str) -> None:
    """Export accepted papers to a JSON file for further analysis.
    
    Args:
        papers: List of accepted papers
        query: Research query string
        output_file: Output file path (if empty string, skips file writing)
    """
    if not output_file:
        return  # Skip export if output_file is empty
    
    results = {
        "query": query,
        "total_accepted": len(papers),
        "papers": [
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "year": p.year,
                "citation_count": p.citation_count,
                "discovered_from": p.discovered_from,
                "edge_type": p.edge_type.value,
                "depth": p.depth,
                "judge_reason": p.judge_reason,
                "judge_confidence": p.judge_confidence,
                "abstract": p.abstract[:500] if p.abstract else None,
            }
            for p in papers
        ],
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
