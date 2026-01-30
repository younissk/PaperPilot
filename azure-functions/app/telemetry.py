"""Telemetry helpers for Azure Functions logging."""

from __future__ import annotations

import logging
from typing import Any


def log_event(logger: logging.Logger, level: int, event_name: str, **dimensions: Any) -> None:
    """Log an event with Application Insights custom dimensions."""
    if dimensions:
        logger.log(level, event_name, extra={"custom_dimensions": dimensions})
    else:
        logger.log(level, event_name)
