"""Async utilities for per-event-loop primitives."""

from __future__ import annotations

import asyncio
from weakref import WeakKeyDictionary

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
    return semaphore
