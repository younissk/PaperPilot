"""Unit tests for API Lambda helper functions."""

import pytest
from decimal import Decimal
from hypothesis import given, strategies as st

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestConvertFloatsToDecimal:
    """Tests for convert_floats_to_decimal function."""

    def test_converts_simple_float(self):
        """Single float is converted to Decimal."""
        # Import here to avoid module-level import issues
        from services.api.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal(3.14)
        assert result == Decimal("3.14")
        assert isinstance(result, Decimal)

    def test_preserves_integers(self):
        """Integers are not converted."""
        from services.api.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal(42)
        assert result == 42
        assert isinstance(result, int)

    def test_preserves_strings(self):
        """Strings are not converted."""
        from services.api.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal("hello")
        assert result == "hello"

    def test_converts_nested_dict(self):
        """Floats in nested dicts are converted."""
        from services.api.handler import convert_floats_to_decimal

        input_dict = {
            "k_factor": 32.0,
            "nested": {"value": 1.5, "count": 10},
            "name": "test",
        }
        result = convert_floats_to_decimal(input_dict)

        assert result["k_factor"] == Decimal("32.0")
        assert result["nested"]["value"] == Decimal("1.5")
        assert result["nested"]["count"] == 10
        assert result["name"] == "test"

    def test_converts_list_of_floats(self):
        """Floats in lists are converted."""
        from services.api.handler import convert_floats_to_decimal

        input_list = [1.1, 2, "three", 4.4]
        result = convert_floats_to_decimal(input_list)

        assert result[0] == Decimal("1.1")
        assert result[1] == 2
        assert result[2] == "three"
        assert result[3] == Decimal("4.4")

    def test_handles_none(self):
        """None values are preserved."""
        from services.api.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal(None)
        assert result is None

    def test_handles_empty_structures(self):
        """Empty dicts and lists are preserved."""
        from services.api.handler import convert_floats_to_decimal

        assert convert_floats_to_decimal({}) == {}
        assert convert_floats_to_decimal([]) == []

    @given(st.floats(allow_nan=False, allow_infinity=False))
    def test_any_float_converts_to_decimal(self, value):
        """Property test: any valid float converts to Decimal."""
        from services.api.handler import convert_floats_to_decimal

        result = convert_floats_to_decimal(value)
        assert isinstance(result, Decimal)


class TestConvertDecimalToNative:
    """Tests for convert_decimal_to_native function."""

    def test_converts_decimal_to_int_when_whole(self):
        """Whole Decimals become ints."""
        from services.api.handler import convert_decimal_to_native

        result = convert_decimal_to_native(Decimal("42"))
        assert result == 42
        assert isinstance(result, int)

    def test_converts_decimal_to_float_when_fractional(self):
        """Fractional Decimals become floats."""
        from services.api.handler import convert_decimal_to_native

        result = convert_decimal_to_native(Decimal("3.14"))
        assert result == 3.14
        assert isinstance(result, float)

    def test_preserves_regular_values(self):
        """Non-Decimal values are preserved."""
        from services.api.handler import convert_decimal_to_native

        assert convert_decimal_to_native("hello") == "hello"
        assert convert_decimal_to_native(42) == 42
        assert convert_decimal_to_native(3.14) == 3.14

    def test_converts_nested_dict(self):
        """Decimals in nested dicts are converted."""
        from services.api.handler import convert_decimal_to_native

        input_dict = {
            "step": Decimal("5"),
            "score": Decimal("0.85"),
            "nested": {"count": Decimal("10")},
        }
        result = convert_decimal_to_native(input_dict)

        assert result["step"] == 5
        assert isinstance(result["step"], int)
        assert result["score"] == 0.85
        assert isinstance(result["score"], float)
        assert result["nested"]["count"] == 10

    def test_converts_list_of_decimals(self):
        """Decimals in lists are converted."""
        from services.api.handler import convert_decimal_to_native

        input_list = [Decimal("1"), Decimal("2.5"), "three"]
        result = convert_decimal_to_native(input_list)

        assert result[0] == 1
        assert isinstance(result[0], int)
        assert result[1] == 2.5
        assert isinstance(result[1], float)
        assert result[2] == "three"

    def test_roundtrip_conversion(self, sample_job_payload):
        """Roundtrip: float -> Decimal -> native preserves values."""
        from services.api.handler import convert_floats_to_decimal, convert_decimal_to_native

        decimalized = convert_floats_to_decimal(sample_job_payload)
        restored = convert_decimal_to_native(decimalized)

        # Values should be equivalent (though types may differ for whole numbers)
        assert restored["k_factor"] == sample_job_payload["k_factor"]
        assert restored["num_results"] == sample_job_payload["num_results"]


class TestPydanticSchemas:
    """Tests for Pydantic request/response schemas."""

    def test_pipeline_request_validation(self):
        """PipelineRequest validates input correctly."""
        from services.api.handler import PipelineRequest

        # Valid request
        request = PipelineRequest(query="test query")
        assert request.query == "test query"
        assert request.num_results == 5  # default
        assert request.k_factor == 32.0  # default

    def test_pipeline_request_with_all_fields(self):
        """PipelineRequest accepts all fields."""
        from services.api.handler import PipelineRequest

        request = PipelineRequest(
            query="test",
            num_results=10,
            max_iterations=8,
            max_accepted=100,
            top_n=30,
            k_factor=64.0,
            pairing="random",
            early_stop=False,
            elo_concurrency=10,
            report_top_k=20,
        )
        assert request.num_results == 10
        assert request.k_factor == 64.0
        assert request.pairing == "random"

    def test_pipeline_request_validation_bounds(self):
        """PipelineRequest enforces field bounds."""
        from services.api.handler import PipelineRequest
        from pydantic import ValidationError

        # num_results out of bounds
        with pytest.raises(ValidationError):
            PipelineRequest(query="test", num_results=0)

        with pytest.raises(ValidationError):
            PipelineRequest(query="test", num_results=101)

    def test_search_request_validation(self):
        """SearchRequest validates input correctly."""
        from services.api.handler import SearchRequest

        request = SearchRequest(query="search test")
        assert request.query == "search test"
        assert request.num_results == 5

    def test_job_response_schema(self):
        """JobResponse handles all fields correctly."""
        from services.api.handler import JobResponse

        response = JobResponse(
            job_id="123",
            job_type="pipeline",
            status="running",
            query="test",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:01:00Z",
            progress={"step": 1, "message": "Processing"},
            result=None,
            error_message=None,
        )
        assert response.job_id == "123"
        assert response.progress["step"] == 1
