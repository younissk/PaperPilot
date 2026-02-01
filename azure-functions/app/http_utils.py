"""HTTP helpers for Azure Functions (CORS + safe responses)."""

from __future__ import annotations

import json
from typing import Any, Callable

import azure.functions as func

from .config import DEBUG, logger


def cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def json_response(payload: dict[str, Any], status: int = 200) -> func.HttpResponse:
    headers = {
        "Content-Type": "application/json",
        **cors_headers(),
    }
    return func.HttpResponse(json.dumps(payload, default=str), status_code=status, headers=headers)


def cors_preflight() -> func.HttpResponse:
    return func.HttpResponse("", status_code=204, headers=cors_headers())


def safe(handler: Callable[[], func.HttpResponse]) -> func.HttpResponse:
    try:
        return handler()
    except Exception as exc:
        logger.exception("Unhandled request error: %s", exc)
        message = "Internal server error"
        if DEBUG:
            message = f"{message}: {exc}"
        return json_response({"error": message}, status=500)
