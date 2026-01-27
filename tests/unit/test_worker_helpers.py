"""Unit tests for Worker Lambda helper functions."""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings
from decimal import Decimal

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestSlugify:
    """Tests for the slugify function."""

    def test_basic_query(self):
        """Basic query is slugified correctly."""
        from services.worker.handler import slugify

        result = slugify("LLM Based Recommender Systems")
        assert result == "llm_based_recommender_systems"

    def test_preserves_hyphens_as_underscores(self):
        """Hyphens become underscores."""
        from services.worker.handler import slugify

        result = slugify("multi-modal LLMs")
        assert result == "multi_modal_llms"

    def test_removes_special_characters(self):
        """Special characters are removed."""
        from services.worker.handler import slugify

        result = slugify("AI in Healthcare: A Review!")
        assert result == "ai_in_healthcare_a_review"

    def test_collapses_multiple_spaces(self):
        """Multiple spaces become single underscore."""
        from services.worker.handler import slugify

        result = slugify("AI    in   healthcare")
        assert result == "ai_in_healthcare"

    def test_strips_leading_trailing_underscores(self):
        """Leading/trailing underscores are stripped."""
        from services.worker.handler import slugify

        result = slugify("  test query  ")
        assert result == "test_query"

    def test_truncates_long_queries(self):
        """Long queries are truncated to 100 characters."""
        from services.worker.handler import slugify

        long_query = "a" * 150
        result = slugify(long_query)
        assert len(result) == 100

    def test_empty_string(self):
        """Empty string returns empty slug."""
        from services.worker.handler import slugify

        result = slugify("")
        assert result == ""

    def test_unicode_characters(self):
        """Unicode characters are handled."""
        from services.worker.handler import slugify

        result = slugify("café neural networks")
        # \w includes unicode word characters
        assert "caf" in result

    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_never_exceeds_100_chars(self, query):
        """Property test: slug never exceeds 100 characters."""
        from services.worker.handler import slugify

        result = slugify(query)
        assert len(result) <= 100

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'))))
    @settings(max_examples=50)
    def test_no_special_chars_in_output(self, query):
        """Property test: output contains only word chars and underscores."""
        from services.worker.handler import slugify
        import re

        result = slugify(query)
        if result:  # Non-empty result
            assert re.match(r'^[\w]+$', result), f"Invalid slug: {result}"


class TestAppendEvent:
    """Tests for the append_event function."""

    def test_appends_event_to_empty_list(self):
        """Event is appended to empty list."""
        from services.worker.handler import append_event

        events: list[dict] = []
        result = append_event(events, "progress", "search", "Starting search")

        assert len(result) == 1
        assert result[0]["type"] == "progress"
        assert result[0]["phase"] == "search"
        assert result[0]["message"] == "Starting search"
        assert "ts" in result[0]

    def test_appends_event_to_existing_list(self):
        """Event is appended to existing list."""
        from services.worker.handler import append_event

        events = [{"type": "start", "phase": "init", "message": "Initialized", "ts": "2024-01-01T00:00:00Z"}]
        result = append_event(events, "progress", "search", "Searching")

        assert len(result) == 2
        assert result[1]["type"] == "progress"

    def test_includes_additional_kwargs(self):
        """Additional kwargs are included in event."""
        from services.worker.handler import append_event

        events: list[dict] = []
        result = append_event(events, "progress", "search", "Found papers", step=1, count=10)

        assert result[0]["step"] == 1
        assert result[0]["count"] == 10

    def test_timestamp_is_iso_format(self):
        """Timestamp is in ISO format."""
        from services.worker.handler import append_event

        events: list[dict] = []
        result = append_event(events, "test", "test", "test")

        ts = result[0]["ts"]
        # Should be parseable as ISO format
        datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_bounds_events_list(self):
        """Events list is bounded to MAX_EVENTS."""
        from services.worker.handler import append_event, MAX_EVENTS

        # Create list with MAX_EVENTS items
        events = [{"type": f"event{i}", "phase": "test", "message": f"msg{i}", "ts": "2024-01-01T00:00:00Z"}
                  for i in range(MAX_EVENTS)]

        result = append_event(events, "new", "test", "new message")

        assert len(result) == MAX_EVENTS
        # First event should have been removed
        assert result[-1]["type"] == "new"


class TestConvertFloatsToDecimalWorker:
    """Tests for convert_floats_to_decimal in worker (same as API)."""

    def test_converts_float(self):
        """Float is converted to Decimal."""
        from services.worker.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal(3.14159)
        assert isinstance(result, Decimal)
        assert result == Decimal("3.14159")

    def test_converts_nested_structure(self):
        """Nested structure has floats converted."""
        from services.worker.handler import convert_floats_to_decimal

        input_data = {
            "progress": {
                "step": 1,
                "score": 0.85,
            },
            "items": [1.1, 2.2, 3.3],
        }
        result = convert_floats_to_decimal(input_data)

        assert result["progress"]["step"] == 1
        assert isinstance(result["progress"]["score"], Decimal)
        assert all(isinstance(x, Decimal) for x in result["items"])


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        """JobStatus has expected values."""
        from services.worker.handler import JobStatus

        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"

    def test_status_is_string_enum(self):
        """JobStatus values are strings."""
        from services.worker.handler import JobStatus

        assert isinstance(JobStatus.QUEUED.value, str)
        assert str(JobStatus.RUNNING) == "running"
