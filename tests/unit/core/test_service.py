"""Unit tests for core service workflow behavior."""

import json
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")

import papernavigator.service as service
from papernavigator.models import AcceptedPaper, EdgeType, QueryProfile

pytestmark = pytest.mark.unit


class _EmptyFeed:
    entries: list = []


async def _fake_generate_query_profile(_query: str):
    return object()

async def _fake_generate_query_profile_model(query: str):
    return QueryProfile(
        core_query=query,
        domain_description="test domain",
        required_concepts=["test"],
        required_concept_groups=[["test"]],
        optional_concepts=[],
        exclusion_concepts=[],
        keyword_patterns=[],
        domain_boundaries="",
        fallback_queries=[],
    )


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


async def test_run_search_falls_back_to_openalex_seeds_when_filter_rejects_all(tmp_path, monkeypatch):
    out = tmp_path / "snowball.json"

    async def fake_search_openalex(_session, augmented_queries, _num_results):
        q = augmented_queries[0] if augmented_queries else "q"
        return [
            {
                "id": "https://openalex.org/W1",
                "title": "Fallback Paper 1",
                "abstract": "a" * 200,
                "publication_year": 2020,
                "cited_by_count": 10,
                "source_query": q,
            },
            {
                "id": "https://openalex.org/W2",
                "title": "Fallback Paper 2",
                "abstract": "b" * 200,
                "publication_year": 2019,
                "cited_by_count": 20,
                "source_query": q,
            },
        ]

    async def fake_filter_results(_profile, _all_results):
        return [], None, None

    class FakeSnowballEngine:
        def __init__(self, *_, **__):
            pass

        async def run(self, _session, seeds, _progress_callback=None, _total_iterations=0):
            return [
                AcceptedPaper(
                    paper_id=s.paper_id,
                    title=s.title,
                    abstract=s.abstract,
                    year=s.year,
                    citation_count=s.citation_count,
                    discovered_from=s.discovered_from,
                    edge_type=EdgeType.SEED,
                    depth=0,
                    judge_reason=s.seed_reason or "Seed paper from initial search",
                    judge_confidence=s.seed_confidence if s.seed_confidence is not None else 1.0,
                )
                for s in seeds
            ]

    monkeypatch.setattr(service, "generate_query_profile", _fake_generate_query_profile_model)
    monkeypatch.setattr(service, "augment_search", _fake_augment_search)
    monkeypatch.setattr(service, "search_all_queries", _fake_search_all_queries)
    monkeypatch.setattr(service, "search_openalex", fake_search_openalex)
    monkeypatch.setattr(service, "filter_results", fake_filter_results)
    monkeypatch.setattr(service, "SnowballEngine", FakeSnowballEngine)

    papers = await service.run_search(
        query="test query",
        output_file=str(out),
        num_results=2,
        max_iterations=1,
        max_accepted=10,
        top_n=2,
    )

    assert len(papers) == 2
    assert papers[0].judge_reason.startswith("Fallback seed")
    assert papers[0].judge_confidence == 0.2
    assert out.exists()


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
