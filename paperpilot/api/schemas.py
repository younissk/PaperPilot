"""Pydantic schemas for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field



class SearchRequest(BaseModel):
    """Request schema for starting a search."""
    query: str = Field(..., description="Research topic to search for")
    num_results: int = Field(5, ge=1, le=100, description="Number of results per query variant")
    max_iterations: int = Field(5, ge=1, le=20, description="Maximum snowball iterations")
    max_accepted: int = Field(200, ge=10, description="Maximum total papers to accept")
    top_n: int = Field(50, ge=5, description="Top N candidates to judge per iteration")


class SearchResponse(BaseModel):
    """Response schema for search results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    total_accepted: int = Field(0, description="Number of accepted papers")
    papers: List[dict] = Field(default_factory=list, description="List of accepted papers")
    result_path: Optional[str] = Field(None, description="Path to saved results file")


class PaperResponse(BaseModel):
    """Schema for a single paper in API response."""
    paper_id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    discovered_from: Optional[str] = None
    edge_type: str
    depth: int
    judge_reason: str
    judge_confidence: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"


# Ranking schemas
class RankingRequest(BaseModel):
    """Request schema for Elo ranking."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")
    n_matches: Optional[int] = Field(None, ge=1, description="Number of matches to run (default: papers * 3)")
    k_factor: float = Field(32.0, ge=1.0, le=100.0, description="K-factor for Elo updates")
    pairing: str = Field("swiss", description="Pairing strategy: 'swiss' or 'random'")
    early_stop: bool = Field(True, description="Stop when top-30 rankings stabilize")
    concurrency: int = Field(5, ge=1, le=20, description="Max concurrent API calls")
    tournament: bool = Field(False, description="Use tournament rounds instead of stability-based stopping")


class RankingResponse(BaseModel):
    """Response schema for ranking results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    papers: List[dict] = Field(default_factory=list, description="List of ranked papers")
    result_path: Optional[str] = Field(None, description="Path to saved ranking file")


# Clustering schemas
class ClusteringRequest(BaseModel):
    """Request schema for clustering."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")
    method: str = Field("hdbscan", description="Clustering method: 'hdbscan', 'dbscan', or 'kmeans'")
    n_clusters: Optional[int] = Field(None, ge=2, description="Number of clusters (kmeans only)")
    dim_method: str = Field("umap", description="Dimension reduction: 'umap', 'tsne', or 'pca'")
    eps: Optional[float] = Field(None, ge=0.0, description="Eps parameter for DBSCAN/HDBSCAN")
    min_samples: Optional[int] = Field(None, ge=1, description="Min samples for DBSCAN/HDBSCAN")


class ClusteringResponse(BaseModel):
    """Response schema for clustering results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    clusters_json_path: Optional[str] = Field(None, description="Path to clusters JSON file")
    clusters_html_path: Optional[str] = Field(None, description="Path to clusters HTML visualization")


# Timeline schemas
class TimelineRequest(BaseModel):
    """Request schema for timeline creation."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")


class TimelineResponse(BaseModel):
    """Response schema for timeline results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    timeline_json_path: Optional[str] = Field(None, description="Path to timeline JSON file")
    timeline_html_path: Optional[str] = Field(None, description="Path to timeline HTML visualization")


# Graph schemas
class GraphRequest(BaseModel):
    """Request schema for citation graph building."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")
    direction: str = Field("both", description="Graph direction: 'both', 'citations', or 'references'")
    limit: int = Field(100, ge=1, le=500, description="Maximum refs/cites to fetch per paper")


class GraphResponse(BaseModel):
    """Response schema for graph results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    graph_json_path: Optional[str] = Field(None, description="Path to graph JSON file")
    graph_html_path: Optional[str] = Field(None, description="Path to graph HTML visualization")


# Report schemas
class ReportRequest(BaseModel):
    """Request schema for report generation."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")
    top_k: int = Field(30, ge=1, description="Number of top papers to use")
    elo_file_path: Optional[str] = Field(None, description="Path to Elo ranking file (auto-detected if not provided)")


class ReportResponse(BaseModel):
    """Response schema for report results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    report_path: Optional[str] = Field(None, description="Path to generated report file")


# Everything schemas
class EverythingRequest(BaseModel):
    """Request schema for running all analysis features."""
    query: str = Field(..., description="Research query string")
    file_path: Optional[str] = Field(None, description="Path to snowball results file (if not provided, uses latest for query)")


class EverythingResponse(BaseModel):
    """Response schema for everything results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    generated_files: List[str] = Field(default_factory=list, description="List of generated file paths")


# Results management schemas
class QueryListResponse(BaseModel):
    """Response schema for listing queries."""
    queries: List[str] = Field(..., description="List of query strings with results")


class QueryMetadataResponse(BaseModel):
    """Response schema for query metadata."""
    query: str = Field(..., description="The query string")
    metadata: Dict[str, Any] = Field(..., description="Metadata dictionary")
