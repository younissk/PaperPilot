"""Request parsing helpers for API payloads."""

from __future__ import annotations

from typing import Any

import azure.functions as func


def parse_json(req: func.HttpRequest) -> dict[str, Any] | None:
    try:
        return req.get_json()
    except ValueError:
        return None


def parse_int(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Invalid integer")
    return int(value)


def parse_float(value: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Invalid float")
    return float(value)


def normalize_pipeline_payload(data: dict[str, Any]) -> dict[str, Any]:
    query = str(data.get("query", "")).strip()
    if not query:
        raise ValueError("Missing required field: query")

    return {
        "query": query,
        "num_results": parse_int(data.get("num_results"), 5),
        "max_iterations": parse_int(data.get("max_iterations"), 5),
        "max_accepted": parse_int(data.get("max_accepted"), 200),
        "top_n": parse_int(data.get("top_n"), 50),
        "k_factor": parse_float(data.get("k_factor"), 32.0),
        "pairing": str(data.get("pairing", "swiss")),
        "early_stop": bool(data.get("early_stop", True)),
        "elo_concurrency": parse_int(data.get("elo_concurrency"), 5),
        "report_top_k": parse_int(data.get("report_top_k"), 30),
    }


def normalize_search_payload(data: dict[str, Any]) -> dict[str, Any]:
    query = str(data.get("query", "")).strip()
    if not query:
        raise ValueError("Missing required field: query")

    return {
        "query": query,
        "num_results": parse_int(data.get("num_results"), 5),
        "max_iterations": parse_int(data.get("max_iterations"), 5),
        "max_accepted": parse_int(data.get("max_accepted"), 200),
        "top_n": parse_int(data.get("top_n"), 50),
    }
