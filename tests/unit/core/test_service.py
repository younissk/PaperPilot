"""Unit tests for core service workflow behavior."""

import json
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")

import papernavigator.service as service

pytestmark = pytest.mark.unit


class _EmptyFeed:
    entries: list = []


async def _fake_generate_query_profile(_query: str):
    return object()


async def _fake_augment_search(query: str):
    return [query], None


async def _fake_search_all_queries(_session, augmented_queries, _num_results):
    return [_EmptyFeed() for _ in augmented_queries]


async def _fake_search_openalex(_session, _augmented_queries, _num_results):
    return []


async def _fake_filter_results(_profile, all_results):
    return [], None, None


async def test_run_search_exports_empty_results_when_filter_yields_none(tmp_path, monkeypatch):
    out = tmp_path / "snowball.json"

    monkeypatch.setattr(service, "generate_query_profile", _fake_generate_query_profile)
    monkeypatch.setattr(service, "augment_search", _fake_augment_search)
    monkeypatch.setattr(service, "search_all_queries", _fake_search_all_queries)
    monkeypatch.setattr(service, "search_openalex", _fake_search_openalex)
    monkeypatch.setattr(service, "filter_results", _fake_filter_results)

    papers = await service.run_search(
        query="test query",
        output_file=str(out),
        num_results=1,
        max_iterations=1,
        max_accepted=1,
        top_n=1,
    )

    assert papers == []
    assert out.exists()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["query"] == "test query"
    assert payload["total_accepted"] == 0
    assert payload["papers"] == []


async def test_run_search_exports_empty_results_when_resolution_yields_none(tmp_path, monkeypatch):
    out = tmp_path / "snowball.json"

    async def fake_filter_results(_profile, all_results):
        return all_results, None, None

    async def fake_search_openalex(_session, augmented_queries, _num_results):
        q = augmented_queries[0] if augmented_queries else "q"
        return [
            {
                "id": "https://openalex.org/W123",
                "title": "Test Paper",
                "abstract": "",
                "publication_year": 2024,
                "source_query": q,
            }
        ]

    async def fake_resolve(_session, _filtered_results, _progress_callback=None):
        return []

    monkeypatch.setattr(service, "generate_query_profile", _fake_generate_query_profile)
    monkeypatch.setattr(service, "augment_search", _fake_augment_search)
    monkeypatch.setattr(service, "search_all_queries", _fake_search_all_queries)
    monkeypatch.setattr(service, "search_openalex", fake_search_openalex)
    monkeypatch.setattr(service, "filter_results", fake_filter_results)
    monkeypatch.setattr(service, "_resolve_papers_to_openalex", fake_resolve)

    papers = await service.run_search(
        query="test query",
        output_file=str(out),
        num_results=1,
        max_iterations=1,
        max_accepted=1,
        top_n=1,
    )

    assert papers == []
    assert out.exists()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["query"] == "test query"
    assert payload["total_accepted"] == 0
    assert payload["papers"] == []
