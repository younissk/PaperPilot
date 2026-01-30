"""Pydantic models for report generation.

This module defines the data structures used throughout the report generation
pipeline, including paper cards, report outlines, and the final report format.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PaperCard(BaseModel):
    """Structured citation-safe representation of a paper.
    
    Paper cards are extracted from raw paper data using LLM and provide
    a consistent format for citation-safe report generation.
    """
    id: str = Field(..., description="Paper ID (e.g., W1234567890)")
    title: str = Field(..., description="Paper title")
    claim: str = Field(..., description="One sentence describing the paper's main contribution")
    paradigm_tags: list[str] = Field(
        default_factory=list,
        description="2-4 tags like 'prompting', 'evaluation', 'retrieval'"
    )
    data_benchmark: str | None = Field(
        None,
        description="Dataset or benchmark used (if stated)"
    )
    measured: str | None = Field(
        None,
        description="What is measured/evaluated (if stated)"
    )
    limitation: str | None = Field(
        None,
        description="One limitation mentioned (if stated)"
    )
    key_quote: str | None = Field(
        None,
        description="Key phrase from the abstract (optional)"
    )
    year: int | None = Field(None, description="Publication year")
    citation_count: int = Field(0, description="Total citation count")
    elo_rating: float | None = Field(
        None,
        description="Elo rating from ranking (if available)"
    )


class SectionPlan(BaseModel):
    """Plan for a single section of the report."""
    title: str = Field(..., description="Section title, e.g., 'Prompting-based Approaches'")
    bullet_claims: list[str] = Field(
        default_factory=list,
        description="Placeholder claims to expand in this section"
    )
    relevant_paper_ids: list[str] = Field(
        default_factory=list,
        description="Paper IDs that should be cited in this section"
    )


class ReportOutline(BaseModel):
    """Complete outline for the report."""
    sections: list[SectionPlan] = Field(
        default_factory=list,
        description="List of section plans"
    )


class SentenceAudit(BaseModel):
    """Audit result for a single sentence."""
    sentence: str = Field(..., description="The sentence being audited")
    supported: bool = Field(..., description="Whether the sentence is supported by citations")
    cited_ids: list[str] = Field(
        default_factory=list,
        description="Paper IDs cited in this sentence"
    )
    issue: str | None = Field(
        None,
        description="Description of the issue if not supported"
    )
    suggested_fix: str | None = Field(
        None,
        description="Suggested fix if not supported"
    )


class AuditResult(BaseModel):
    """Complete audit result for a section."""
    section_title: str = Field(..., description="Title of the audited section")
    original_text: str = Field(..., description="Original section text")
    revised_text: str = Field(..., description="Revised section text after audit")
    sentences: list[SentenceAudit] = Field(
        default_factory=list,
        description="Audit results for each sentence"
    )
    supported_count: int = Field(0, description="Number of supported sentences")
    unsupported_count: int = Field(0, description="Number of unsupported sentences")
    revised_count: int = Field(0, description="Number of revised sentences")


class WrittenSection(BaseModel):
    """A written section before or after audit."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content with citations")
    paper_ids_used: list[str] = Field(
        default_factory=list,
        description="Paper IDs actually cited in this section"
    )


class ResearchItem(BaseModel):
    """An item in the current_research list of the report."""
    title: str = Field(..., description="Research theme title")
    summary: str = Field(..., description="Summary of this research theme")
    paper_ids: list[str] = Field(
        default_factory=list,
        description="Paper IDs cited in this item"
    )


class OpenProblem(BaseModel):
    """An open problem identified from the literature."""
    title: str = Field(..., description="Problem title")
    text: str = Field(..., description="Description of the open problem")
    paper_ids: list[str] = Field(
        default_factory=list,
        description="Paper IDs that mention or relate to this problem"
    )


class Report(BaseModel):
    """Final report output structure."""
    query: str = Field(..., description="Original research query")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of generation"
    )
    total_papers_used: int = Field(0, description="Number of papers used in the report")
    introduction: str = Field(..., description="Quick intro to the topic based on query and results")
    current_research: list[ResearchItem] = Field(
        default_factory=list,
        description="Current research themes identified"
    )
    open_problems: list[OpenProblem] = Field(
        default_factory=list,
        description="Open problems identified from the literature"
    )
    conclusion: str = Field(..., description="Concluding summary")
    paper_cards: list[PaperCard] = Field(
        default_factory=list,
        description="All paper cards used for reference"
    )
