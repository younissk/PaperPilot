"""Structured logging configuration for PaperPilot.

This module provides a dual-sink logging system:
- JSON renderer for backend/frontend consumption (machine-readable)
- Rich console renderer for CLI (human-readable)

The logger can be configured at startup to use either renderer based on
whether it's running in CLI mode or API mode.
"""

import logging

import structlog
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)

# structlog.dev.ConsoleRenderer automatically uses Rich if available


def configure_logging(cli_mode: bool = False, log_level: str = "INFO") -> None:
    """Configure structlog with appropriate renderer.
    
    Args:
        cli_mode: If True, use Rich console renderer for pretty CLI output.
                  If False, use JSON renderer for machine-readable logs.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Common processors for all modes
    processors = [
        # Add log level
        add_log_level,
        # Add timestamp
        TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        StackInfoRenderer(),
        # Format exceptions
        format_exc_info,
    ]

    # Choose renderer based on mode
    if cli_mode:
        # ConsoleRenderer automatically uses Rich if available for pretty output
        from structlog.dev import ConsoleRenderer
        renderer = ConsoleRenderer(colors=True)
    else:
        # JSON renderer for backend/API consumption
        renderer = JSONRenderer()

    processors.append(renderer)

    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured logger instance.
    
    Args:
        name: Optional logger name (typically __name__ of the calling module)
        
    Returns:
        Configured structlog logger
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
