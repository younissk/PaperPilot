"""Filter arXiv search results using LLM relevance judgment (Async version).

This module provides async filtering of search results with concurrent
LLM-based relevance judgments for improved performance.
"""

import time

from tqdm.asyncio import tqdm_asyncio

from papernavigator.judge import judge_result
from papernavigator.models import QueryProfile, ReducedArxivEntry


async def filter_results(
    profile: QueryProfile,
    results: list[ReducedArxivEntry]
) -> tuple[list[ReducedArxivEntry], list[ReducedArxivEntry], float]:
    """Filters results using the judge_result function with dynamic profile.
    
    Uses concurrent LLM calls for improved performance.
    
    Args:
        profile: The QueryProfile with domain-specific filtering criteria
        results: List of arXiv entries to filter
    
    Returns:
        Tuple of (filtered_results, discarded_results, time_taken_seconds)
    """

    start_time = time.time()

    # Remove duplicates by title while preserving the objects
    seen_titles: set[str] = set()
    unique_results: list[ReducedArxivEntry] = []
    for r in results:
        if r.title not in seen_titles:
            unique_results.append(r)
            seen_titles.add(r.title)
    results = unique_results

    if not results:
        return [], [], 0.0

    # Create tasks for all judgments
    tasks = [
        judge_result(profile, result.source_query, result)
        for result in results
    ]

    # Run all judgments concurrently with progress bar
    judgments = await tqdm_asyncio.gather(
        *tasks,
        desc="Filtering results",
        total=len(tasks)
    )

    # Separate filtered and discarded based on judgments
    filtered: list[ReducedArxivEntry] = []
    discarded: list[ReducedArxivEntry] = []

    for result, is_relevant in zip(results, judgments):
        if is_relevant:
            filtered.append(result)
        else:
            discarded.append(result)

    end_time = time.time()
    total_time_taken = end_time - start_time

    return filtered, discarded, total_time_taken
