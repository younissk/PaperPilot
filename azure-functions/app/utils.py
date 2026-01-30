"""Utility helpers (time, slugify, secrets)."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime, timedelta

from .config import (
    AZURE_KEY_VAULT_URL,
    OPENAI_API_KEY_SECRET_NAME,
    TTL_DAYS,
    logger,
)

# Maximum time a job can be in "running" state before considered stale (minutes)
MAX_RUNNING_MINUTES = 15


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def is_job_stale(job: dict, max_running_minutes: int = MAX_RUNNING_MINUTES) -> bool:
    """Check if a job in 'running' state is stale (stuck).
    
    A job is considered stale if:
    - Status is 'running'
    - updated_at is more than max_running_minutes ago
    
    Args:
        job: Job document from Cosmos DB
        max_running_minutes: Maximum minutes a job can run before being stale
        
    Returns:
        True if the job is stale and should be retried
    """
    if job.get("status") != "running":
        return False
    
    updated_at = job.get("updated_at")
    if not updated_at:
        # No updated_at timestamp - consider stale
        return True
    
    try:
        # Parse ISO timestamp
        if updated_at.endswith("Z"):
            updated_at = updated_at[:-1] + "+00:00"
        updated_dt = datetime.fromisoformat(updated_at)
        
        # Make timezone-aware if needed
        if updated_dt.tzinfo is None:
            updated_dt = updated_dt.replace(tzinfo=UTC)
        
        elapsed = datetime.now(UTC) - updated_dt
        return elapsed > timedelta(minutes=max_running_minutes)
    except (ValueError, TypeError):
        # Parsing failed - consider stale to allow retry
        return True


def expires_at() -> int:
    return int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())


def slugify(query: str) -> str:
    slug = query.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "_", slug)
    slug = slug.strip("_")
    return slug[:100]


def load_openai_api_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    if not (AZURE_KEY_VAULT_URL and OPENAI_API_KEY_SECRET_NAME):
        logger.warning("OPENAI_API_KEY not set and Key Vault not configured")
        return

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=AZURE_KEY_VAULT_URL, credential=credential)
        secret = client.get_secret(OPENAI_API_KEY_SECRET_NAME)
        os.environ["OPENAI_API_KEY"] = secret.value
        logger.info("Loaded OPENAI_API_KEY from Key Vault")
    except Exception as exc:
        logger.error("Failed to load OPENAI_API_KEY from Key Vault: %s", exc)
        raise
