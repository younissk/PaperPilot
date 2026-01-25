"""Pydantic schemas for API requests and responses."""

from typing import List, Optional
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
    status: str = Field(..., description="Job status: 'running', 'completed', 'failed'")
    query: str = Field(..., description="The search query")
    total_accepted: int = Field(..., description="Number of accepted papers")
    papers: List[dict] = Field(default_factory=list, description="List of accepted papers")


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
