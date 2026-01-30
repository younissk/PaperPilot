"""Unit tests for core domain models."""

import pytest

from papernavigator.models import (
    AcceptedPaper,
    EdgeType,
    JudgmentResult,
    QueryProfile,
    QueueItem,
    SnowballCandidate,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestEdgeType:
    """Tests for EdgeType enum."""

    def test_edge_type_values(self):
        """EdgeType has expected values."""
        assert EdgeType.REFERENCE.value == "reference"
        assert EdgeType.CITATION.value == "citation"
        assert EdgeType.SEED.value == "seed"

    def test_edge_type_is_string_enum(self):
        """EdgeType values are strings."""
        assert isinstance(EdgeType.REFERENCE.value, str)
        assert str(EdgeType.CITATION) == "citation"


class TestSnowballCandidate:
    """Tests for SnowballCandidate model."""

    def test_minimal_candidate(self):
        """SnowballCandidate with minimal fields."""
        candidate = SnowballCandidate(
            paper_id="W123",
            title="Test Paper",
            edge_type=EdgeType.SEED,
            depth=0,
        )
        assert candidate.paper_id == "W123"
        assert candidate.title == "Test Paper"
        assert candidate.abstract is None
        assert candidate.year is None
        assert candidate.citation_count == 0

    def test_full_candidate(self):
        """SnowballCandidate with all fields."""
        candidate = SnowballCandidate(
            paper_id="W123456789",
            title="Large Language Models for Recommendations",
            abstract="This paper explores...",
            year=2024,
            citation_count=150,
            influential_citation_count=25,
            discovered_from="W987654321",
            edge_type=EdgeType.CITATION,
            depth=2,
            priority_score=0.85,
            arxiv_id="2401.12345",
        )
        assert candidate.year == 2024
        assert candidate.citation_count == 150
        assert candidate.discovered_from == "W987654321"
        assert candidate.edge_type == EdgeType.CITATION

    def test_candidate_edge_type_validation(self):
        """EdgeType must be valid."""
        # Valid edge types work
        for edge_type in EdgeType:
            candidate = SnowballCandidate(
                paper_id="test",
                title="Test",
                edge_type=edge_type,
                depth=0,
            )
            assert candidate.edge_type == edge_type


class TestAcceptedPaper:
    """Tests for AcceptedPaper model."""

    def test_accepted_paper_requires_judgment(self):
        """AcceptedPaper requires judgment fields."""
        paper = AcceptedPaper(
            paper_id="W123",
            title="Test Paper",
            edge_type=EdgeType.SEED,
            depth=0,
            judge_reason="Highly relevant to query",
            judge_confidence=0.95,
        )
        assert paper.judge_reason == "Highly relevant to query"
        assert paper.judge_confidence == 0.95

    def test_accepted_paper_optional_fields(self):
        """AcceptedPaper optional fields have correct defaults."""
        paper = AcceptedPaper(
            paper_id="W123",
            title="Test",
            edge_type=EdgeType.SEED,
            depth=0,
            judge_reason="Test",
            judge_confidence=0.9,
        )
        assert paper.abstract is None
        assert paper.year is None
        assert paper.citation_count == 0
        assert paper.discovered_from is None


class TestJudgmentResult:
    """Tests for JudgmentResult model."""

    def test_relevant_judgment(self):
        """JudgmentResult for relevant paper."""
        result = JudgmentResult(
            relevant=True,
            confidence=0.95,
            reason="Paper directly addresses LLMs in recommender systems",
        )
        assert result.relevant is True
        assert result.confidence == 0.95

    def test_irrelevant_judgment(self):
        """JudgmentResult for irrelevant paper."""
        result = JudgmentResult(
            relevant=False,
            confidence=0.85,
            reason="Paper focuses on traditional collaborative filtering",
        )
        assert result.relevant is False

    def test_judgment_confidence_range(self):
        """Confidence should be between 0 and 1."""
        # Valid confidence values
        for conf in [0.0, 0.5, 1.0]:
            result = JudgmentResult(relevant=True, confidence=conf, reason="Test")
            assert result.confidence == conf


class TestQueryProfile:
    """Tests for QueryProfile model."""

    def test_minimal_profile(self):
        """QueryProfile with minimal fields."""
        profile = QueryProfile(
            core_query="LLM recommendations",
            domain_description="Research on using LLMs for recommendation systems",
            required_concepts=["LLM", "recommendation"],
            optional_concepts=["personalization"],
            exclusion_concepts=["traditional CF"],
            keyword_patterns=[r"(?i)llm", r"(?i)recommend"],
            domain_boundaries="In: LLM-based systems. Out: Traditional methods.",
        )
        assert profile.core_query == "LLM recommendations"
        assert len(profile.required_concepts) == 2

    def test_profile_with_concept_groups(self):
        """QueryProfile with concept groups for flexible matching."""
        profile = QueryProfile(
            core_query="test",
            domain_description="test",
            required_concepts=[],
            required_concept_groups=[
                ["LLM", "large language model", "GPT"],
                ["recommendation", "recommender", "suggestions"],
            ],
            optional_concepts=[],
            exclusion_concepts=[],
            keyword_patterns=[],
            domain_boundaries="test",
        )
        assert len(profile.required_concept_groups) == 2
        assert "GPT" in profile.required_concept_groups[0]

    def test_profile_with_fallback_queries(self):
        """QueryProfile with fallback queries."""
        profile = QueryProfile(
            core_query="test",
            domain_description="test",
            required_concepts=[],
            optional_concepts=[],
            exclusion_concepts=[],
            keyword_patterns=[],
            domain_boundaries="test",
            fallback_queries=["recommender systems survey", "LLM applications"],
        )
        assert len(profile.fallback_queries) == 2


class TestQueueItem:
    """Tests for QueueItem model."""

    def test_queue_item_creation(self):
        """QueueItem creation with all fields."""
        item = QueueItem(
            paper_id="W123",
            discovered_from="W456",
            depth=2,
            score=0.85,
        )
        assert item.paper_id == "W123"
        assert item.depth == 2
        assert item.score == 0.85

    def test_queue_item_defaults(self):
        """QueueItem has correct defaults."""
        item = QueueItem(
            paper_id="W123",
            depth=0,
            score=1.0,
        )
        assert item.discovered_from is None
