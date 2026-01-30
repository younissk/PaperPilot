"""Timeline generation for chronological paper analysis.

This module provides functionality to create timelines from snowball results,
grouping papers by publication year and visualizing the chronological evolution
of research in a domain.

WHY: Understanding the temporal distribution of papers helps identify trends,
     evolution of research themes, and key time periods in a field.
HOW: 1. Extract papers with year information from snowball.json
     2. Group papers by year (and optionally by month)
     3. Generate JSON timeline data structure
     4. Create interactive HTML visualization
"""

from collections import defaultdict
from typing import Any


def create_timeline(papers: list[dict[str, Any]], query: str) -> dict[str, Any]:
    """Create a timeline structure from a list of papers.
    
    Args:
        papers: List of paper dictionaries with 'year' field
        query: Research query string
        
    Returns:
        Timeline data dictionary with years, timeline array, and metadata
    """
    # Group papers by year
    papers_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for paper in papers:
        year = paper.get("year")
        if year is not None:
            papers_by_year[year].append(paper)

    # Sort years
    sorted_years = sorted(papers_by_year.keys())

    # Build timeline array
    timeline = []
    for year in sorted_years:
        year_papers = papers_by_year[year]
        timeline.append({
            "year": year,
            "count": len(year_papers),
            "papers": sorted(
                year_papers,
                key=lambda p: p.get("citation_count", 0),
                reverse=True
            )
        })

    # Convert years dict to string keys for JSON serialization
    years_dict = {str(year): papers for year, papers in papers_by_year.items()}

    return {
        "query": query,
        "total_papers": len(papers),
        "years": years_dict,
        "timeline": timeline,
        "year_range": {
            "min": min(sorted_years) if sorted_years else None,
            "max": max(sorted_years) if sorted_years else None,
        },
    }
