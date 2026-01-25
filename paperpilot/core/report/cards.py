"""Paper card generation using LLM.

This module extracts structured paper cards from raw paper data using async
LLM calls with batch processing and rate limiting.
"""

import asyncio
import json
import os
import time
from typing import Optional

from openai import AsyncOpenAI

from paperpilot.core.logging import get_logger
from paperpilot.core.report.models import PaperCard

log = get_logger(__name__)

# Async OpenAI client
_async_client: Optional[AsyncOpenAI] = None

# Concurrency limits
OPENAI_MAX_CONCURRENT = 20
_openai_semaphore: Optional[asyncio.Semaphore] = None


def _get_async_client() -> AsyncOpenAI:
    """Get or create the async OpenAI client."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _async_client


def _get_semaphore() -> asyncio.Semaphore:
    """Get or create the concurrency semaphore."""
    global _openai_semaphore
    if _openai_semaphore is None:
        _openai_semaphore = asyncio.Semaphore(OPENAI_MAX_CONCURRENT)
    return _openai_semaphore


def _build_card_prompt(paper: dict) -> str:
    """Build the prompt for extracting a paper card."""
    title = paper.get("title", "Unknown")
    abstract = paper.get("abstract", "") or "(No abstract available)"
    
    return f"""Given this academic paper's title and abstract, extract structured information.

Title: {title}

Abstract: {abstract}

Extract the following as JSON:
1. "claim": One sentence (max 30 words) describing the paper's main contribution or finding
2. "paradigm_tags": List of 2-4 research paradigm tags from this set: 
   [prompting, fine-tuning, retrieval, generative, evaluation, benchmark, 
    fairness, efficiency, multimodal, reasoning, agents, knowledge, 
    representation, training, inference, application, survey, dataset]
3. "data_benchmark": The primary dataset or benchmark used (null if not clearly stated)
4. "measured": What metrics or outcomes are measured/evaluated (null if not clearly stated)  
5. "limitation": One key limitation mentioned by the authors (null if not stated)
6. "key_quote": One important phrase (5-15 words) from the abstract that captures the essence

Return ONLY valid JSON with these exact keys. Use null for missing values."""


async def generate_paper_card(paper: dict) -> Optional[PaperCard]:
    """Extract a structured card from a single paper using LLM.
    
    Args:
        paper: Paper dictionary with title, abstract, paper_id, etc.
        
    Returns:
        PaperCard if successful, None if extraction fails
    """
    paper_id = paper.get("paper_id", "unknown")
    title = paper.get("title", "Unknown")[:50]
    
    log.debug("generating_card", paper_id=paper_id, title=title)
    
    prompt = _build_card_prompt(paper)
    client = _get_async_client()
    semaphore = _get_semaphore()
    
    try:
        async with semaphore:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
        
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        
        # Build the PaperCard with extracted data + original metadata
        card = PaperCard(
            id=paper_id,
            title=paper.get("title", "Unknown"),
            claim=data.get("claim", "No claim extracted"),
            paradigm_tags=data.get("paradigm_tags", []),
            data_benchmark=data.get("data_benchmark"),
            measured=data.get("measured"),
            limitation=data.get("limitation"),
            key_quote=data.get("key_quote"),
            year=paper.get("year"),
            citation_count=paper.get("citation_count", 0),
            elo_rating=paper.get("elo_rating"),
        )
        
        log.info("card_generated", paper_id=paper_id, tags=card.paradigm_tags)
        return card
        
    except json.JSONDecodeError as e:
        log.error("card_json_parse_error", paper_id=paper_id, error=str(e))
        return None
    except Exception as e:
        log.error("card_generation_failed", paper_id=paper_id, error=str(e))
        return None


async def generate_paper_cards(papers: list[dict]) -> list[PaperCard]:
    """Generate paper cards for a batch of papers concurrently.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        List of successfully generated PaperCards
    """
    if not papers:
        log.warning("no_papers_to_process")
        return []
    
    log.info("batch_card_generation_start", total_papers=len(papers))
    start_time = time.time()
    
    # Process all papers concurrently
    tasks = [generate_paper_card(paper) for paper in papers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful results
    cards: list[PaperCard] = []
    failed = 0
    
    for result in results:
        if isinstance(result, PaperCard):
            cards.append(result)
        elif isinstance(result, Exception):
            log.error("card_task_exception", error=str(result))
            failed += 1
        else:
            # None result from failed extraction
            failed += 1
    
    duration = time.time() - start_time
    log.info(
        "batch_card_generation_complete",
        success=len(cards),
        failed=failed,
        duration_sec=round(duration, 2)
    )
    
    return cards
