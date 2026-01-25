from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None


class Link(BaseModel):
    href: str
    rel: str
    type: Optional[str] = None
    title: Optional[str] = None


class Category(BaseModel):
    term: str
    scheme: str


class ArxivEntry(BaseModel):
    id: str
    title: str
    updated: str
    published: str
    summary: str
    authors: List[Author] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    categories: List[Category] = Field(default_factory=list)
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    primary_category: Optional[str] = None


class ArxivFeed(BaseModel):
    id: str
    title: str
    updated: str
    totalResults: int
    startIndex: int
    itemsPerPage: int
    entries: List[ArxivEntry] = Field(default_factory=list)


class ReducedArxivEntry(BaseModel):
    title: str
    updated: str
    summary: str
    link: str
    source_query: str  # Tracks which query variant found this paper


class QueryProfile(BaseModel):
    """Dynamic relevance profile generated from the user's search query.

    This model holds criteria for filtering academic papers based on
    an arbitrary research topic, replacing hardcoded domain logic.
    """
    core_query: str  # The original user query
    domain_description: str  # Human-readable description of the research domain
    # Concepts that MUST appear (e.g., ["LLM", "recommender systems"])
    required_concepts: List[str]
    # Grouped concepts: OR within group, AND across groups
    # e.g., [["LLM", "large language model"], ["recommender", "recommendation"]]
    required_concept_groups: List[List[str]] = Field(default_factory=list)
    optional_concepts: List[str]  # Concepts that boost relevance if present
    # Concepts that indicate irrelevance (negative filter)
    exclusion_concepts: List[str]
    keyword_patterns: List[str]  # Regex patterns for fast keyword gating
    domain_boundaries: str  # Description of what is IN vs OUT of scope
    # Fallback queries for discovering foundational papers in each concept domain
    fallback_queries: List[str] = Field(default_factory=list)


class QueueItem(BaseModel):
    # Canonical identifier (e.g., Semantic Scholar paperId or DOI)
    paper_id: str
    # Which seed paper and which edge type (reference or citation)
    discovered_from: Optional[str] = None
    depth: int  # Exploration depth in citation/reference graph
    score: float  # Priority score for processing


class EdgeType(str, Enum):
    """Type of edge in the citation graph."""
    REFERENCE = "reference"  # backward link (paper cites this)
    CITATION = "citation"    # forward link (this cites paper)
    SEED = "seed"            # initial seed paper


class SnowballCandidate(BaseModel):
    """A candidate paper discovered during snowballing expansion."""
    paper_id: str                              # OpenAlex or Semantic Scholar ID
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    influential_citation_count: int = 0
    discovered_from: Optional[str] = None      # parent paper_id
    edge_type: EdgeType
    depth: int
    priority_score: float = 0.0
    arxiv_id: Optional[str] = None             # arXiv ID for S2 fallback


class AcceptedPaper(BaseModel):
    """A paper that passed LLM relevance judgment."""
    paper_id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    discovered_from: Optional[str] = None
    edge_type: EdgeType
    depth: int
    judge_reason: str
    judge_confidence: float


class JudgmentResult(BaseModel):
    """Structured result from LLM relevance judgment."""
    relevant: bool
    confidence: float
    reason: str
