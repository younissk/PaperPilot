"""Request parsing helpers for API payloads."""

from __future__ import annotations

import re
from typing import Any

import azure.functions as func

# Simple email regex for validation (not exhaustive, but catches common errors)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def parse_json(req: func.HttpRequest) -> dict[str, Any] | None:
    try:
        return req.get_json()
    except ValueError:
        return None


def parse_email(value: Any) -> str | None:
    """Parse and validate an optional email address.

    Returns None if not provided, raises ValueError if invalid format.
    """
    if value is None:
        return None
    email = str(value).strip().lower()
    if not email:
        return None
    if not EMAIL_REGEX.match(email):
        raise ValueError(f"Invalid email format: {value}")
    return email


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
        "notification_email": parse_email(data.get("notification_email")),
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
