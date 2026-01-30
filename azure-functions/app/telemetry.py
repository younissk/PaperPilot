"""Telemetry helpers for Azure Functions logging."""

from __future__ import annotations

import logging
from typing import Any


def log_event(logger: logging.Logger, level: int, message: str, **dimensions: Any) -> None:
    """Log a message with Application Insights custom dimensions."""
    if dimensions:
        logger.log(level, message, extra={"custom_dimensions": dimensions})
    else:
        logger.log(level, message)
