"""Citation/reference graph building for paper connections.

This module provides functionality to build citation and reference graphs
from snowball results, showing how papers in the collection are connected
through citations and references.

WHY: Understanding citation networks reveals research lineages, influential
     papers, and how ideas flow through a research domain.
HOW: 1. Extract paper IDs from snowball.json
     2. Fetch references and citations from OpenAlex API
     3. Filter to only include connections within the snowball set
     4. Build graph structure (nodes and edges)
     5. Generate JSON and HTML visualization
"""

from typing import Any, Literal

import aiohttp

from papernavigator.openalex import (
    extract_openalex_id,
    get_citations,
    get_references,
)


async def build_citation_graph(
    session: aiohttp.ClientSession,
    papers: list[dict[str, Any]],
    query: str = "Unknown",
    direction: Literal["both", "citations", "references"] = "both",
    limit: int = 100,
) -> dict[str, Any]:
    """Build a citation/reference graph from papers.
    
    Args:
        session: aiohttp ClientSession for API calls
        papers: List of paper dictionaries with 'paper_id' (OpenAlex IDs)
        direction: Which connections to include: "both", "citations", or "references"
        limit: Maximum number of refs/cites to fetch per paper
        
    Returns:
        Graph data dictionary with nodes and edges
    """
    # Create set of paper IDs in the snowball for fast lookup
    paper_ids: set[str] = set()
    paper_map: dict[str, dict[str, Any]] = {}

    for paper in papers:
        paper_id = paper.get("paper_id")
        if paper_id:
            # Normalize OpenAlex ID format
            if not paper_id.startswith("W"):
                paper_id = f"W{paper_id}"
            paper_ids.add(paper_id)
            paper_map[paper_id] = paper

    # Build nodes list
    nodes = []
    for paper_id, paper in paper_map.items():
        nodes.append({
            "id": paper_id,
            "title": paper.get("title", "Unknown"),
            "year": paper.get("year"),
            "citation_count": paper.get("citation_count", 0),
            "abstract": paper.get("abstract"),
        })

    # Build edges by fetching references and/or citations
    edges = []
    edge_set: set[tuple[str, str, str]] = set()  # (source, target, type) to avoid duplicates

    for paper in papers:
        paper_id = paper.get("paper_id")
        if not paper_id:
            continue

        # Normalize ID
        if not paper_id.startswith("W"):
            paper_id = f"W{paper_id}"

        # Fetch references (papers this paper cites)
        if direction in ["both", "references"]:
            try:
                refs = await get_references(session, paper_id, limit=limit, verbose=False)
                for ref in refs:
                    ref_id = extract_openalex_id(ref)
                    if ref_id:
                        # Normalize ID format
                        if not ref_id.startswith("W"):
                            ref_id = f"W{ref_id}"
                        if ref_id in paper_ids:
                            # Edge: paper_id cites ref_id (backward reference)
                            edge_key = (paper_id, ref_id, "cites")
                            if edge_key not in edge_set:
                                edge_set.add(edge_key)
                                edges.append({
                                    "source": paper_id,
                                    "target": ref_id,
                                    "type": "cites",
                                    "direction": "backward",  # paper cites reference (backward in time)
                                })
            except Exception:
                # Skip if API call fails
                pass

        # Fetch citations (papers that cite this paper)
        if direction in ["both", "citations"]:
            try:
                cites = await get_citations(session, paper_id, limit=limit, verbose=False)
                for cite in cites:
                    cite_id = extract_openalex_id(cite)
                    if cite_id:
                        # Normalize ID format
                        if not cite_id.startswith("W"):
                            cite_id = f"W{cite_id}"
                        if cite_id in paper_ids:
                            # Edge: cite_id cites paper_id (forward citation)
                            edge_key = (cite_id, paper_id, "cited_by")
                            if edge_key not in edge_set:
                                edge_set.add(edge_key)
                                edges.append({
                                    "source": cite_id,
                                    "target": paper_id,
                                    "type": "cited_by",
                                    "direction": "forward",  # citation cites paper (forward in time)
                                })
            except Exception:
                # Skip if API call fails
                pass

    return {
        "query": query,
        "total_papers": len(nodes),
        "total_edges": len(edges),
        "direction": direction,
        "limit": limit,
        "nodes": nodes,
        "edges": edges,
    }
