"""Unit tests for report models and serialization."""

from datetime import datetime

import pytest

from papernavigator.report.models import (
    AuditResult,
    OpenProblem,
    PaperCard,
    Report,
    ReportOutline,
    ResearchItem,
    SectionPlan,
    SentenceAudit,
    WrittenSection,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestPaperCard:
    """Tests for PaperCard model."""

    def test_minimal_paper_card(self):
        """PaperCard with only required fields."""
        card = PaperCard(
            id="W123456789",
            title="Test Paper",
            claim="This paper introduces a novel approach to X.",
        )
        assert card.id == "W123456789"
        assert card.title == "Test Paper"
        assert card.paradigm_tags == []
        assert card.data_benchmark is None
        assert card.citation_count == 0

    def test_full_paper_card(self):
        """PaperCard with all fields."""
        card = PaperCard(
            id="W123456789",
            title="LLMs for Recommendations",
            claim="This paper demonstrates that LLMs can improve recommendation accuracy.",
            paradigm_tags=["prompting", "evaluation", "retrieval"],
            data_benchmark="MovieLens-1M",
            measured="recommendation accuracy (NDCG@10)",
            limitation="Limited to movie domain",
            key_quote="LLMs significantly outperform traditional methods",
            year=2024,
            citation_count=150,
            elo_rating=1650.5,
        )
        assert len(card.paradigm_tags) == 3
        assert card.year == 2024
        assert card.elo_rating == 1650.5

    def test_paper_card_serialization(self):
        """PaperCard can be serialized to dict."""
        card = PaperCard(
            id="W123",
            title="Test",
            claim="Test claim",
            year=2024,
        )
        data = card.model_dump()

        assert isinstance(data, dict)
        assert data["id"] == "W123"
        assert data["year"] == 2024


class TestSectionPlan:
    """Tests for SectionPlan model."""

    def test_section_plan_creation(self):
        """SectionPlan with required fields."""
        plan = SectionPlan(
            title="Prompting-based Approaches",
            bullet_claims=[
                "LLMs can be prompted for recommendations",
                "Chain-of-thought improves results",
            ],
            relevant_paper_ids=["W123", "W456", "W789"],
        )
        assert plan.title == "Prompting-based Approaches"
        assert len(plan.bullet_claims) == 2
        assert len(plan.relevant_paper_ids) == 3

    def test_section_plan_defaults(self):
        """SectionPlan has empty defaults."""
        plan = SectionPlan(title="Test Section")
        assert plan.bullet_claims == []
        assert plan.relevant_paper_ids == []


class TestReportOutline:
    """Tests for ReportOutline model."""

    def test_report_outline_creation(self):
        """ReportOutline with sections."""
        outline = ReportOutline(
            sections=[
                SectionPlan(title="Introduction", bullet_claims=["Overview"]),
                SectionPlan(title="Methods", bullet_claims=["Approach"]),
            ]
        )
        assert len(outline.sections) == 2

    def test_report_outline_empty(self):
        """ReportOutline can be empty."""
        outline = ReportOutline()
        assert outline.sections == []


class TestSentenceAudit:
    """Tests for SentenceAudit model."""

    def test_supported_sentence(self):
        """Audit of a supported sentence."""
        audit = SentenceAudit(
            sentence="LLMs improve recommendations [W123].",
            supported=True,
            cited_ids=["W123"],
        )
        assert audit.supported is True
        assert audit.issue is None

    def test_unsupported_sentence(self):
        """Audit of an unsupported sentence."""
        audit = SentenceAudit(
            sentence="LLMs always work perfectly.",
            supported=False,
            cited_ids=[],
            issue="Claim not supported by any citation",
            suggested_fix="Add citation or rephrase as hypothesis",
        )
        assert audit.supported is False
        assert audit.issue is not None


class TestAuditResult:
    """Tests for AuditResult model."""

    def test_audit_result_creation(self):
        """AuditResult with full data."""
        result = AuditResult(
            section_title="Methods",
            original_text="Original content here.",
            revised_text="Revised content with citations.",
            sentences=[
                SentenceAudit(sentence="Test.", supported=True, cited_ids=["W1"]),
            ],
            supported_count=1,
            unsupported_count=0,
            revised_count=0,
        )
        assert result.supported_count == 1
        assert len(result.sentences) == 1


class TestWrittenSection:
    """Tests for WrittenSection model."""

    def test_written_section(self):
        """WrittenSection with content."""
        section = WrittenSection(
            title="Results",
            content="The results show [W123] that performance improved.",
            paper_ids_used=["W123"],
        )
        assert section.title == "Results"
        assert "W123" in section.paper_ids_used


class TestResearchItem:
    """Tests for ResearchItem model."""

    def test_research_item(self):
        """ResearchItem creation."""
        item = ResearchItem(
            title="Prompting Strategies",
            summary="Various prompting strategies have been explored...",
            paper_ids=["W123", "W456"],
        )
        assert item.title == "Prompting Strategies"
        assert len(item.paper_ids) == 2


class TestOpenProblem:
    """Tests for OpenProblem model."""

    def test_open_problem(self):
        """OpenProblem creation."""
        problem = OpenProblem(
            title="Scalability",
            text="Current approaches struggle with large catalogs.",
            paper_ids=["W789"],
        )
        assert problem.title == "Scalability"


class TestReport:
    """Tests for Report model."""

    def test_minimal_report(self):
        """Report with minimal fields."""
        report = Report(
            query="LLM recommendations",
            introduction="This report surveys...",
            conclusion="In conclusion...",
        )
        assert report.query == "LLM recommendations"
        assert report.total_papers_used == 0
        assert report.current_research == []
        assert report.paper_cards == []

    def test_full_report(self):
        """Report with all fields."""
        report = Report(
            query="LLM recommendations",
            total_papers_used=10,
            introduction="This report surveys LLM-based recommendations.",
            current_research=[
                ResearchItem(
                    title="Prompting",
                    summary="Prompting approaches...",
                    paper_ids=["W1"],
                ),
            ],
            open_problems=[
                OpenProblem(
                    title="Scalability",
                    text="Scaling remains a challenge.",
                    paper_ids=["W2"],
                ),
            ],
            conclusion="In conclusion, LLMs show promise.",
            paper_cards=[
                PaperCard(id="W1", title="Paper 1", claim="Claim 1"),
                PaperCard(id="W2", title="Paper 2", claim="Claim 2"),
            ],
        )
        assert report.total_papers_used == 10
        assert len(report.current_research) == 1
        assert len(report.open_problems) == 1
        assert len(report.paper_cards) == 2

    def test_report_generated_at_default(self):
        """Report has generated_at timestamp by default."""
        report = Report(
            query="test",
            introduction="intro",
            conclusion="conclusion",
        )
        # Should be a valid ISO timestamp
        datetime.fromisoformat(report.generated_at)

    def test_report_serialization(self):
        """Report can be serialized to dict."""
        report = Report(
            query="test",
            introduction="intro",
            conclusion="conclusion",
        )
        data = report.model_dump()

        assert isinstance(data, dict)
        assert data["query"] == "test"
        assert "generated_at" in data

    def test_report_json_serialization(self):
        """Report can be serialized to JSON."""
        report = Report(
            query="test",
            introduction="intro",
            conclusion="conclusion",
            paper_cards=[
                PaperCard(id="W1", title="Paper 1", claim="Claim 1"),
            ],
        )
        json_str = report.model_dump_json()

        assert isinstance(json_str, str)
        assert "test" in json_str
        assert "W1" in json_str
