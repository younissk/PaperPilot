"""Results management API routes."""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from paperpilot.api.schemas import (
    QueryListResponse,
    QueryMetadataResponse,
)
from paperpilot.core.results import ResultsManager

router = APIRouter(prefix="/api/results", tags=["results"])

results_manager = ResultsManager()


@router.get("", response_model=QueryListResponse)
async def list_queries():
    """List all queries that have results."""
    queries = results_manager.list_queries()
    return QueryListResponse(queries=queries)


@router.get("/{query}", response_model=QueryMetadataResponse)
async def get_query_metadata(query: str):
    """Get metadata for a specific query."""
    metadata = results_manager.get_metadata(query)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Query not found: {query}")
    return QueryMetadataResponse(query=query, metadata=metadata)


@router.get("/{query}/snowball")
async def get_snowball_results(query: str):
    """Get snowball results for a query."""
    snowball_path = results_manager.get_latest_snowball(query)
    if snowball_path is None:
        raise HTTPException(status_code=404, detail=f"Snowball results not found for query: {query}")
    
    try:
        with open(snowball_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in results file: {e}")


@router.get("/{query}/elo")
async def get_elo_results(query: str):
    """Get Elo ranking results for a query."""
    elo_path = results_manager.get_latest_elo(query)
    if elo_path is None:
        raise HTTPException(status_code=404, detail=f"Elo ranking results not found for query: {query}")
    
    try:
        with open(elo_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in results file: {e}")


@router.get("/{query}/clusters")
async def get_clusters_results(query: str):
    """Get clustering results for a query."""
    metadata = results_manager.get_metadata(query)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Query not found: {query}")
    
    clusters_json = metadata.get("clusters_json")
    if not clusters_json:
        raise HTTPException(status_code=404, detail=f"Clustering results not found for query: {query}")
    
    query_dir = results_manager.get_query_dir(query)
    clusters_path = query_dir / clusters_json
    
    if not clusters_path.exists():
        raise HTTPException(status_code=404, detail=f"Clusters file not found: {clusters_json}")
    
    try:
        with open(clusters_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in clusters file: {e}")


@router.get("/{query}/timeline")
async def get_timeline_results(query: str):
    """Get timeline results for a query."""
    metadata = results_manager.get_metadata(query)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Query not found: {query}")
    
    timeline_json = metadata.get("timeline_json")
    if not timeline_json:
        raise HTTPException(status_code=404, detail=f"Timeline results not found for query: {query}")
    
    query_dir = results_manager.get_query_dir(query)
    timeline_path = query_dir / timeline_json
    
    if not timeline_path.exists():
        raise HTTPException(status_code=404, detail=f"Timeline file not found: {timeline_json}")
    
    try:
        with open(timeline_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in timeline file: {e}")


@router.get("/{query}/graph")
async def get_graph_results(query: str):
    """Get graph results for a query."""
    metadata = results_manager.get_metadata(query)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Query not found: {query}")
    
    graph_json = metadata.get("graph_json")
    if not graph_json:
        raise HTTPException(status_code=404, detail=f"Graph results not found for query: {query}")
    
    query_dir = results_manager.get_query_dir(query)
    graph_path = query_dir / graph_json
    
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail=f"Graph file not found: {graph_json}")
    
    try:
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in graph file: {e}")


@router.get("/{query}/report")
async def get_report_results(query: str):
    """Get report results for a query."""
    metadata = results_manager.get_metadata(query)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Query not found: {query}")
    
    report_file = metadata.get("report_file")
    if not report_file:
        raise HTTPException(status_code=404, detail=f"Report results not found for query: {query}")
    
    query_dir = results_manager.get_query_dir(query)
    report_path = query_dir / report_file
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report file not found: {report_file}")
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in report file: {e}")


@router.get("/{query}/files/{filename}")
async def download_file(query: str, filename: str):
    """Download a specific file from a query's results directory."""
    query_dir = results_manager.get_query_dir(query)
    file_path = query_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Determine media type based on extension
    media_type = "application/json"
    if filename.endswith(".html"):
        media_type = "text/html"
    elif filename.endswith(".json"):
        media_type = "application/json"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )
