from enum import Enum

from pydantic import BaseModel, Field


class Author(BaseModel):
    name: str
    affiliation: str | None = None


class Link(BaseModel):
    href: str
    rel: str
    type: str | None = None
    title: str | None = None


class Category(BaseModel):
    term: str
    scheme: str


class ArxivEntry(BaseModel):
    id: str
    title: str
    updated: str
    published: str
    summary: str
    authors: list[Author] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    comment: str | None = None
    journal_ref: str | None = None
    doi: str | None = None
    primary_category: str | None = None


class ArxivFeed(BaseModel):
    id: str
    title: str
    updated: str
    totalResults: int
    startIndex: int
    itemsPerPage: int
    entries: list[ArxivEntry] = Field(default_factory=list)


class ReducedArxivEntry(BaseModel):
    """A paper result from search (arXiv or OpenAlex).
    
    Despite the name, this model is now used for results from multiple sources.
    """
    title: str
    updated: str
    summary: str
    link: str | None = None  # arXiv link or OpenAlex URL
    source_query: str  # Tracks which query variant found this paper
    source: str = "arxiv"  # "arxiv" or "openalex"
    openalex_id: str | None = None  # Pre-resolved OpenAlex ID (for OpenAlex-sourced papers)


class QueryProfile(BaseModel):
    """Dynamic relevance profile generated from the user's search query.

    This model holds criteria for filtering academic papers based on
    an arbitrary research topic, replacing hardcoded domain logic.
    """
    core_query: str  # The original user query
    domain_description: str  # Human-readable description of the research domain
    # Concepts that MUST appear (e.g., ["LLM", "recommender systems"])
    required_concepts: list[str]
    # Grouped concepts: OR within group, AND across groups
    # e.g., [["LLM", "large language model"], ["recommender", "recommendation"]]
    required_concept_groups: list[list[str]] = Field(default_factory=list)
    optional_concepts: list[str]  # Concepts that boost relevance if present
    # Concepts that indicate irrelevance (negative filter)
    exclusion_concepts: list[str]
    keyword_patterns: list[str]  # Regex patterns for fast keyword gating
    domain_boundaries: str  # Description of what is IN vs OUT of scope
    # Fallback queries for discovering foundational papers in each concept domain
    fallback_queries: list[str] = Field(default_factory=list)


class QueueItem(BaseModel):
    # Canonical identifier (e.g., Semantic Scholar paperId or DOI)
    paper_id: str
    # Which seed paper and which edge type (reference or citation)
    discovered_from: str | None = None
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
    abstract: str | None = None
    year: int | None = None
    citation_count: int = 0
    influential_citation_count: int = 0
    discovered_from: str | None = None      # parent paper_id
    edge_type: EdgeType
    depth: int
    priority_score: float = 0.0
    arxiv_id: str | None = None             # arXiv ID for S2 fallback
    # Optional metadata for seed papers (used when we fall back to "best available"
    # seeds after strict filtering yields zero papers).
    seed_reason: str | None = None
    seed_confidence: float | None = None


class AcceptedPaper(BaseModel):
    """A paper that passed LLM relevance judgment."""
    paper_id: str
    title: str
    abstract: str | None = None
    year: int | None = None
    citation_count: int = 0
    discovered_from: str | None = None
    edge_type: EdgeType
    depth: int
    judge_reason: str
    judge_confidence: float


class JudgmentResult(BaseModel):
    """Structured result from LLM relevance judgment."""
    relevant: bool
    confidence: float
    reason: str
