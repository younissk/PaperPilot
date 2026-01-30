"""Async utilities for per-event-loop primitives."""

from __future__ import annotations

import asyncio
from weakref import WeakKeyDictionary

from papernavigator.logging import get_logger

log = get_logger(__name__)

# Map of name -> WeakKeyDictionary[loop, semaphore]
_semaphores: dict[str, WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]] = {}


def get_loop_semaphore(name: str, max_concurrent: int) -> asyncio.Semaphore:
    """Return a semaphore bound to the current event loop."""
    loop = asyncio.get_running_loop()
    bucket = _semaphores.setdefault(name, WeakKeyDictionary())
    semaphore = bucket.get(loop)
    if semaphore is None:
        semaphore = asyncio.Semaphore(max_concurrent)
        bucket[loop] = semaphore
        log.debug("semaphore_created", name=name, max_concurrent=max_concurrent, loop_id=id(loop))
    return semaphore


def validate_loop(obj: object, name: str) -> None:
    """Raise a clear error if an asyncio object is bound to a different loop."""
    try:
        loop = asyncio.get_running_loop()
        bound_loop = getattr(obj, "_loop", None)
        if bound_loop is not None and bound_loop is not loop:
            message = (
                f"Async object '{name}' is bound to a different event loop "
                f"(current={id(loop)}, bound={id(bound_loop)})."
            )
            log.error("loop_mismatch", name=name, current_loop=id(loop), bound_loop=id(bound_loop))
            raise RuntimeError(message)
    except RuntimeError:
        # get_running_loop raises RuntimeError if no loop; re-raise for clarity
        raise
