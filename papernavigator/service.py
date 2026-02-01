"""Core service layer for PaperPilot search workflow.

This module provides the main search service without any presentation
dependencies (no Rich, no console output). It returns data structures
that can be used by CLI, API, or other interfaces.
"""

import asyncio
import json
import os
from collections.abc import Callable
from typing import Any

import aiohttp

from papernavigator.augment import augment_search
from papernavigator.filter import filter_results
from papernavigator.models import (
    AcceptedPaper,
    EdgeType,
    QueryProfile,
    ReducedArxivEntry,
    SnowballCandidate,
)
from papernavigator.openalex import (
    extract_arxiv_id,
    extract_openalex_id,
    get_work_details,
    resolve_arxiv_to_openalex,
    resolve_by_title,
    search_papers as search_openalex,
)
from papernavigator.profiler import generate_query_profile
from papernavigator.search import search_all_queries
from papernavigator.snowball import SnowballEngine


def _relax_profile_for_recall(profile: QueryProfile) -> QueryProfile:
    """Create a more recall-oriented variant of a QueryProfile.

    Used only when strict filtering rejects all retrieved papers.
    """
    relaxed = profile.model_copy(deep=True)

    if relaxed.required_concept_groups:
        relaxed.required_concept_groups = relaxed.required_concept_groups[:2]
        relaxed.required_concepts = [
            term for group in relaxed.required_concept_groups for term in group
        ]

    recall_boundary = (
        "IN scope: papers plausibly related to the CORE query, including partial matches "
        "and foundational/methodological work. OUT of scope: clearly unrelated domains."
    )
    if relaxed.domain_boundaries:
        relaxed.domain_boundaries = f"{relaxed.domain_boundaries}\n\n{recall_boundary}"
    else:
        relaxed.domain_boundaries = recall_boundary

    return relaxed


async def _build_fallback_seeds_from_openalex(
    session: aiohttp.ClientSession,
    *,
    query: str,
    profile: QueryProfile,
    initial_openalex_results: list[dict[str, Any]],
    seed_count: int,
    num_results_per_query: int,
) -> list[SnowballCandidate]:
    """Build 'best available' OpenAlex seeds when strict filtering yields zero papers."""

    candidates: list[dict[str, Any]] = list(initial_openalex_results)

    fallback_queries = (profile.fallback_queries or [])[:8]
    if fallback_queries:
        extra = await search_openalex(
            session,
            fallback_queries,
            num_results_per_query=min(5, num_results_per_query),
            min_citations=0,
        )
        candidates.extend(extra)

    by_id: dict[str, dict[str, Any]] = {}
    for work in candidates:
        work_id = str(work.get("id", ""))
        if not work_id:
            continue
        openalex_id = work_id.replace("https://openalex.org/", "")
        if not openalex_id:
            continue
        by_id.setdefault(openalex_id, work)

    unique = list(by_id.items())
    unique.sort(
        key=lambda item: (
            int(item[1].get("cited_by_count", 0) or 0),
            len(item[1].get("abstract") or ""),
        ),
        reverse=True,
    )

    picked = unique[: max(1, seed_count)]

    seeds: list[SnowballCandidate] = []
    for openalex_id, work in picked:
        seeds.append(
            SnowballCandidate(
                paper_id=openalex_id,
                title=str(work.get("title", "")),
                abstract=work.get("abstract") or None,
                year=work.get("publication_year"),
                citation_count=int(work.get("cited_by_count", 0) or 0),
                influential_citation_count=0,
                discovered_from=str(work.get("source_query") or f"{query} (fallback)"),
                edge_type=EdgeType.SEED,
                depth=0,
                arxiv_id=None,
                seed_reason="Fallback seed (no papers passed initial relevance filtering)",
                seed_confidence=0.2,
            )
        )

    return seeds


async def run_search(
    query: str,
    num_results: int = 15,
    output_file: str = "snowball_results.json",
    max_iterations: int = 5,
    max_accepted: int = 200,
    top_n: int = 50,
    progress_callback: Callable[[int, str, int, int, str, int, int], None] | None = None,
) -> list[AcceptedPaper]:
    """Run the full PaperPilot search workflow (async version).
    
    Args:
        query: Research topic to search for
        num_results: Number of results per query variant
        output_file: Output file for results
        max_iterations: Maximum snowball iterations
        max_accepted: Maximum total papers to accept
        top_n: Top N candidates to judge per iteration
        progress_callback: Optional callback function(step, step_name, current, total, message, current_iteration, total_iterations)
        
    Returns:
        List of accepted papers
    """
    # Create shared aiohttp session for all HTTP requests
    async with aiohttp.ClientSession() as session:
        # Step 0: Generate query profile
        if progress_callback:
            progress_callback(0, "Generating Query Profile", 0, 0, "Analyzing query to extract concepts...", 0, max_iterations)
        profile = await generate_query_profile(query)
        profile_for_snowball = profile

        # Step 1: Augment the search query
        if progress_callback:
            progress_callback(1, "Augmenting Search Query", 0, 0, "Creating query variants...", 0, max_iterations)
        augmented_queries, _ = await augment_search(query)

        # Step 2: Search arXiv AND OpenAlex in parallel for all query variants
        if progress_callback:
            progress_callback(2, "Searching Sources", 0, len(augmented_queries), f"Searching arXiv + OpenAlex for {len(augmented_queries)} query variants...", 0, max_iterations)
        
        # Run both searches concurrently
        arxiv_task = search_all_queries(session, augmented_queries, num_results)
        openalex_task = search_openalex(session, augmented_queries, num_results)
        
        feeds, openalex_results = await asyncio.gather(arxiv_task, openalex_task)

        # Collect arXiv results
        all_results: list[ReducedArxivEntry] = []

        for idx, (search_query, feed) in enumerate(zip(augmented_queries, feeds), 1):
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
                    source="arxiv",
                ))
        
        arxiv_count = len(all_results)
        
        # Convert and add OpenAlex results
        for work in openalex_results:
            openalex_id = work.get("id", "").replace("https://openalex.org/", "")
            all_results.append(ReducedArxivEntry(
                title=work.get("title", ""),
                updated=str(work.get("publication_year", "")),
                summary=work.get("abstract") or "",
                link=work.get("id"),  # OpenAlex URL
                source_query=work.get("source_query", ""),
                source="openalex",
                openalex_id=openalex_id if openalex_id else None,
            ))
        
        openalex_count = len(all_results) - arxiv_count
        
        # Deduplicate by title (case-insensitive)
        seen_titles: set[str] = set()
        unique_results: list[ReducedArxivEntry] = []
        for result in all_results:
            title_lower = result.title.lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_results.append(result)
        
        all_results = unique_results
        
        if progress_callback:
            progress_callback(2, "Searching Sources", len(augmented_queries), len(augmented_queries), f"Found {arxiv_count} from arXiv, {openalex_count} from OpenAlex ({len(all_results)} unique)", 0, max_iterations)

        # Step 3: Filter results for relevance (CONCURRENT LLM calls)
        if progress_callback:
            progress_callback(3, "Filtering Results", 0, len(all_results), f"Filtering {len(all_results)} papers for relevance...", 0, max_iterations)
        filtered_results, _, _ = await filter_results(profile, all_results)

        if progress_callback:
            progress_callback(3, "Filtering Results", len(filtered_results), len(all_results), f"Filtered to {len(filtered_results)} relevant papers", 0, max_iterations)

        if not filtered_results and all_results:
            profile_for_snowball = _relax_profile_for_recall(profile)
            if progress_callback:
                progress_callback(
                    3,
                    "Filtering Results",
                    0,
                    len(all_results),
                    "No papers passed strict filtering; retrying with a recall-oriented profile...",
                    0,
                    max_iterations,
                )
            filtered_results, _, _ = await filter_results(profile_for_snowball, all_results)
            if progress_callback:
                progress_callback(
                    3,
                    "Filtering Results",
                    len(filtered_results),
                    len(all_results),
                    f"Recall-oriented filtering kept {len(filtered_results)} papers",
                    0,
                    max_iterations,
                )

        if not filtered_results:
            # If we found papers but filtered them all out, fall back to "best available"
            # OpenAlex seeds so the pipeline can still produce something useful.
            if all_results and openalex_results:
                try:
                    configured = int(os.getenv("PAPERPILOT_FALLBACK_SEED_COUNT", "8") or "8")
                except ValueError:
                    configured = 8
                fallback_seed_count = min(configured, max(1, num_results))
                if progress_callback:
                    progress_callback(
                        3,
                        "Filtering Results",
                        0,
                        0,
                        f"Falling back to {fallback_seed_count} high-signal OpenAlex seed papers...",
                        0,
                        max_iterations,
                    )

                seeds = await _build_fallback_seeds_from_openalex(
                    session,
                    query=query,
                    profile=profile_for_snowball,
                    initial_openalex_results=openalex_results,
                    seed_count=fallback_seed_count,
                    num_results_per_query=num_results,
                )

                if seeds:
                    if progress_callback:
                        progress_callback(
                            5,
                            "Running Snowball Search",
                            0,
                            0,
                            f"Starting snowball search with {len(seeds)} fallback seed papers...",
                            0,
                            max_iterations,
                        )

                    engine = SnowballEngine(
                        profile=profile_for_snowball,
                        max_iterations=max_iterations,
                        top_n_per_iteration=top_n,
                        min_new_papers_threshold=3,
                        max_total_accepted=max_accepted,
                    )
                    accepted_papers = await engine.run(session, seeds, progress_callback, max_iterations)

                    if progress_callback:
                        progress_callback(
                            6,
                            "Exporting Results",
                            0,
                            0,
                            f"Saving {len(accepted_papers)} papers to file...",
                            max_iterations,
                            max_iterations,
                        )
                    export_results(accepted_papers, query, output_file)
                    return accepted_papers

            # Ensure downstream consumers (pipeline, UI, artifacts) always have a snowball JSON,
            # even when no papers pass filtering/resolution.
            export_results([], query, output_file)
            return []

        # Step 4: Resolve arXiv papers to OpenAlex IDs (CONCURRENT)
        if progress_callback:
            progress_callback(4, "Resolving Paper IDs", 0, len(filtered_results), f"Resolving {len(filtered_results)} papers to OpenAlex IDs...", 0, max_iterations)
        seeds = await _resolve_papers_to_openalex(session, filtered_results, progress_callback)

        if progress_callback:
            progress_callback(4, "Resolving Paper IDs", len(seeds), len(filtered_results), f"Resolved {len(seeds)} papers to OpenAlex IDs", 0, max_iterations)

        if not seeds:
            export_results([], query, output_file)
            return []

        # Step 5: Run the Snowball Engine
        if progress_callback:
            progress_callback(5, "Running Snowball Search", 0, 0, f"Starting snowball search with {len(seeds)} seed papers...", 0, max_iterations)
        engine = SnowballEngine(
            profile=profile_for_snowball,
            max_iterations=max_iterations,
            top_n_per_iteration=top_n,
            min_new_papers_threshold=3,
            max_total_accepted=max_accepted,
        )

        accepted_papers = await engine.run(session, seeds, progress_callback, max_iterations)

        # Step 6: Export results
        if progress_callback:
            progress_callback(6, "Exporting Results", 0, 0, f"Saving {len(accepted_papers)} papers to file...", max_iterations, max_iterations)
        export_results(accepted_papers, query, output_file)

        if progress_callback:
            progress_callback(6, "Exporting Results", 1, 1, f"Completed! Found {len(accepted_papers)} papers", max_iterations, max_iterations)

        return accepted_papers


async def _resolve_papers_to_openalex(
    session: aiohttp.ClientSession,
    filtered_results: list[ReducedArxivEntry],
    progress_callback: Callable[[int, str, int, int, str, int, int], None] | None = None,
) -> list[SnowballCandidate]:
    """Resolve papers to OpenAlex IDs concurrently.
    
    Papers from OpenAlex already have IDs and skip resolution.
    Papers from arXiv are resolved via DOI or title search.
    
    Args:
        session: aiohttp ClientSession
        filtered_results: List of filtered search results (from arXiv or OpenAlex)
        
    Returns:
        List of SnowballCandidate objects (successfully resolved papers)
    """

    async def resolve_single_paper(result: ReducedArxivEntry) -> tuple[ReducedArxivEntry, SnowballCandidate | None]:
        """Resolve a single paper, returning (result, candidate or None)."""
        
        # OpenAlex-sourced papers already have IDs - no resolution needed
        if result.source == "openalex" and result.openalex_id:
            # Fetch additional details if needed
            details = await get_work_details(session, result.openalex_id)
            
            seed = SnowballCandidate(
                paper_id=result.openalex_id,
                title=result.title,
                abstract=result.summary,
                year=details.get("publication_year") if details else None,
                citation_count=details.get("cited_by_count", 0) if details else 0,
                influential_citation_count=0,
                discovered_from=result.source_query,
                edge_type=EdgeType.SEED,
                depth=0,
                arxiv_id=None,  # OpenAlex papers don't have arXiv IDs
            )
            return result, seed
        
        # arXiv-sourced papers need resolution
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
    seeds: list[SnowballCandidate] = []

    for idx, (result, seed) in enumerate(results, 1):
        if seed:
            seeds.append(seed)
        if progress_callback and idx % 5 == 0:  # Update every 5 papers
            progress_callback(4, "Resolving Paper IDs", idx, len(filtered_results), f"Resolved {idx} of {len(filtered_results)} papers...", 0, 0)

    return seeds


def export_results(papers: list[AcceptedPaper], query: str, output_file: str) -> None:
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
