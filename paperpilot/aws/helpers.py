"""Shared helper functions for AWS Lambda handlers.

This module contains utilities shared between the API and Worker Lambda handlers:
- JobStatus enum for consistent job state tracking
- Decimal conversion functions for DynamoDB compatibility
- Query slugification for S3 paths
"""

import re
from decimal import Decimal
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Job status values used by both API and Worker.
    
    These values are stored in DynamoDB and used for job state tracking.
    """
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def convert_floats_to_decimal(obj: Any) -> Any:
    """Recursively convert floats to Decimals for DynamoDB compatibility.
    
    DynamoDB doesn't support Python floats natively, so we convert them
    to Decimal before storing.
    
    Args:
        obj: Any Python object (dict, list, float, etc.)
        
    Returns:
        The same structure with floats replaced by Decimals.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj


def convert_decimal_to_native(obj: Any) -> Any:
    """Recursively convert Decimals back to int/float for JSON serialization.
    
    When reading from DynamoDB, numeric values come back as Decimal.
    This converts them back to native Python types for JSON responses.
    
    Args:
        obj: Any Python object (dict, list, Decimal, etc.)
        
    Returns:
        The same structure with Decimals replaced by int/float.
    """
    if isinstance(obj, Decimal):
        # Convert to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_native(item) for item in obj]
    return obj


def slugify(query: str) -> str:
    """Convert query to a filesystem-safe slug for S3 paths.
    
    This creates a URL-safe, lowercase string from a query that can be
    used as a directory name in S3 or for URL paths.
    
    Args:
        query: The research query string.
        
    Returns:
        A slugified version of the query (e.g., "LLM Based Recommender" -> "llm_based_recommender")
    """
    slug = query.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '_', slug)
    slug = slug.strip('_')
    if len(slug) > 100:
        slug = slug[:100]
    return slug
