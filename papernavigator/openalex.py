"""OpenAlex API client for citation graph exploration (Async version).

This module provides async functions to interact with the OpenAlex API
for resolving paper IDs, fetching metadata, and retrieving citation/reference links.

OpenAlex is a free, open catalog of the global research system with 250M+ works.
API Documentation: https://docs.openalex.org/

Key features used:
- referenced_works: List of works this paper cites (backward links)
- cites filter: Get works that cite a given paper (forward links)
- cited_by_count: Number of citations
"""

import asyncio
import os
import re
import urllib.parse
from typing import Any

import aiohttp

from papernavigator.async_utils import get_loop_semaphore, validate_loop
from papernavigator.logging import get_logger

logger = get_logger(__name__)

# Configuration
OPENALEX_API_BASE = "https://api.openalex.org"
OPENALEX_RATE_LIMIT_DELAY = 0.1  # OpenAlex is generous with rate limits
OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")  # Optional: for polite pool

# Concurrency limits
OPENALEX_MAX_CONCURRENT = 10

# Semantic Scholar config
SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_RATE_LIMIT_DELAY = 1.0  # S2 is more restrictive
SEMANTIC_SCHOLAR_MAX_CONCURRENT = 1

# Fields to select for efficiency
WORK_SELECT_FIELDS = "id,title,abstract_inverted_index,publication_year,cited_by_count,referenced_works,authorships,type"


def _get_openalex_semaphore() -> asyncio.Semaphore:
    """Get or create the OpenAlex semaphore for rate limiting."""
    semaphore = get_loop_semaphore("openalex", OPENALEX_MAX_CONCURRENT)
    validate_loop(semaphore, "openalex_semaphore")
    return semaphore


def _get_s2_semaphore() -> asyncio.Semaphore:
    """Get or create the Semantic Scholar semaphore for rate limiting."""
    semaphore = get_loop_semaphore("semantic_scholar", SEMANTIC_SCHOLAR_MAX_CONCURRENT)
    validate_loop(semaphore, "semantic_scholar_semaphore")
    return semaphore


def _build_headers() -> dict[str, str]:
    """Build request headers, optionally with email for polite pool."""
    headers = {"Accept": "application/json"}
    if OPENALEX_EMAIL:
        headers["User-Agent"] = f"mailto:{OPENALEX_EMAIL}"
    return headers


async def _make_request(
    session: aiohttp.ClientSession,
    url: str,
    retries: int = 3,
    use_semaphore: bool = True
) -> dict[str, Any] | None:
    """Make an async HTTP request to the OpenAlex API with retry logic.
    
    Args:
        session: aiohttp ClientSession
        url: The API endpoint URL
        retries: Number of retries on failure
        use_semaphore: Whether to use semaphore for rate limiting
        
    Returns:
        Parsed JSON response or None on failure
    """
    semaphore = _get_openalex_semaphore() if use_semaphore else asyncio.Semaphore(1)

    async with semaphore:
        await asyncio.sleep(OPENALEX_RATE_LIMIT_DELAY)

        for attempt in range(retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 404:
                        return None
                    elif response.status == 429:
                        wait_time = (attempt + 1) * 2
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status >= 400:
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
                        continue

                    return await response.json()
            except TimeoutError:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
            except aiohttp.ClientError:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(1)

    return None


def _decode_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Decode OpenAlex inverted index abstract to plain text.
    
    OpenAlex stores abstracts as inverted indexes for legal reasons.
    This reconstructs the original text.
    
    Args:
        inverted_index: Dict mapping words to their positions
        
    Returns:
        Reconstructed abstract string or None
    """
    if not inverted_index:
        return None

    # Reconstruct the abstract from inverted index
    words_with_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words_with_positions.append((pos, word))

    # Sort by position and join
    words_with_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in words_with_positions)


def extract_arxiv_id(link_or_id: str) -> str | None:
    """Extract arXiv ID from various formats.
    
    Handles:
    - http://arxiv.org/abs/2301.12345
    - https://arxiv.org/abs/2301.12345v1
    - http://arxiv.org/pdf/2301.12345.pdf
    - 2301.12345
    - arXiv:2301.12345
    
    Args:
        link_or_id: arXiv link or ID string
        
    Returns:
        Clean arXiv ID (e.g., "2301.12345") or None
    """
    # Pattern for arXiv IDs (new format: YYMM.NNNNN, old format: category/YYMMNNN)
    new_format = r'(\d{4}\.\d{4,5})'
    old_format = r'([a-z-]+/\d{7})'

    # Try new format first
    match = re.search(new_format, link_or_id)
    if match:
        return match.group(1)

    # Try old format
    match = re.search(old_format, link_or_id)
    if match:
        return match.group(1)

    return None


def extract_openalex_id(work_data: dict[str, Any]) -> str | None:
    """Extract the OpenAlex ID from a work data dict.
    
    Args:
        work_data: Work metadata dictionary
        
    Returns:
        OpenAlex ID (e.g., "W1234567890") or None
    """
    if "id" in work_data:
        return work_data["id"].replace("https://openalex.org/", "")
    return None


async def resolve_arxiv_to_openalex(
    session: aiohttp.ClientSession,
    arxiv_link_or_id: str
) -> str | None:
    """Convert an arXiv ID or link to an OpenAlex work ID.
    
    Strategy:
    1. Try DOI lookup (arXiv papers often have DOIs like 10.48550/arXiv.XXXX.XXXXX)
    2. Fall back to title search if that fails
    
    Args:
        session: aiohttp ClientSession
        arxiv_link_or_id: arXiv link or ID
        
    Returns:
        OpenAlex work ID (e.g., "W1234567890") or None
    """
    arxiv_id = extract_arxiv_id(arxiv_link_or_id)
    if not arxiv_id:
        return None

    # Try arXiv DOI format
    arxiv_doi = f"10.48550/arXiv.{arxiv_id}"
    url = f"{OPENALEX_API_BASE}/works/doi:{arxiv_doi}"

    result = await _make_request(session, url)

    if result and "id" in result:
        # Extract just the ID part (W1234567890)
        openalex_id = result["id"].replace("https://openalex.org/", "")
        return openalex_id

    return None


async def resolve_by_doi(
    session: aiohttp.ClientSession,
    doi: str
) -> str | None:
    """Resolve a DOI to an OpenAlex work ID.
    
    Args:
        session: aiohttp ClientSession
        doi: DOI string (with or without https://doi.org/ prefix)
        
    Returns:
        OpenAlex work ID or None
    """
    # Clean the DOI
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

    url = f"{OPENALEX_API_BASE}/works/doi:{doi}"

    result = await _make_request(session, url)

    if result and "id" in result:
        return result["id"].replace("https://openalex.org/", "")

    return None


async def resolve_by_title(
    session: aiohttp.ClientSession,
    title: str
) -> dict[str, Any] | None:
    """Search for a work by title and return its details.
    
    Args:
        session: aiohttp ClientSession
        title: Paper title to search for
        
    Returns:
        Work data dict or None
    """
    encoded_title = urllib.parse.quote(title)
    url = f"{OPENALEX_API_BASE}/works?filter=title.search:{encoded_title}&per_page=1"

    result = await _make_request(session, url)

    if result and "results" in result and len(result["results"]) > 0:
        return result["results"][0]

    return None


async def get_work_details(
    session: aiohttp.ClientSession,
    openalex_id: str
) -> dict[str, Any] | None:
    """Fetch detailed metadata for a work by its OpenAlex ID.
    
    Args:
        session: aiohttp ClientSession
        openalex_id: OpenAlex work ID (e.g., "W2741809807")
        
    Returns:
        Dictionary with work metadata or None
    """
    # Ensure proper format
    if not openalex_id.startswith("W"):
        openalex_id = f"W{openalex_id}"

    url = f"{OPENALEX_API_BASE}/works/{openalex_id}"

    result = await _make_request(session, url)

    if result:
        # Decode abstract if present
        if "abstract_inverted_index" in result:
            result["abstract"] = _decode_abstract(result.get("abstract_inverted_index"))

    return result


async def batch_get_work_details(
    session: aiohttp.ClientSession,
    openalex_ids: list[str]
) -> list[dict[str, Any] | None]:
    """Fetch details for multiple works concurrently.
    
    Args:
        session: aiohttp ClientSession
        openalex_ids: List of OpenAlex work IDs
        
    Returns:
        List of work metadata dictionaries (None for failed lookups)
    """
    tasks = [get_work_details(session, oid) for oid in openalex_ids]
    return await asyncio.gather(*tasks)


async def get_references(
    session: aiohttp.ClientSession,
    openalex_id: str,
    limit: int = 100,
    verbose: bool = True
) -> list[dict[str, Any]]:
    """Get papers that this paper cites (backward links / references).
    
    Uses the referenced_works field from the work, then fetches details
    for each referenced work.
    
    Args:
        session: aiohttp ClientSession
        openalex_id: OpenAlex work ID
        limit: Maximum number of references to return
        verbose: Whether to print debug information
        
    Returns:
        List of work metadata dictionaries
    """
    # Ensure proper format
    if not openalex_id.startswith("W"):
        openalex_id = f"W{openalex_id}"

    # First get the work to access referenced_works
    work = await get_work_details(session, openalex_id)
    if not work:
        if verbose:
            logger.debug("Could not fetch work details", openalex_id=openalex_id)
        return []

    referenced_ids = work.get("referenced_works", [])
    refs_count = work.get("referenced_works_count", 0)

    if verbose:
        logger.debug(
            "Work reference counts",
            openalex_id=openalex_id,
            reported_count=refs_count,
            actual_list_length=len(referenced_ids)
        )

    if not referenced_ids:
        if verbose:
            logger.debug("No referenced_works found in OpenAlex", openalex_id=openalex_id)
        return []

    # Limit the number of references
    referenced_ids = referenced_ids[:limit]

    # Batch fetch referenced works (OpenAlex allows up to 50 IDs per request)
    references = []
    batch_size = 50

    # Create tasks for all batches
    async def fetch_batch(batch: list[str]) -> list[dict[str, Any]]:
        batch_ids = [ref.replace("https://openalex.org/", "") for ref in batch]
        ids_filter = "|".join(batch_ids)
        url = f"{OPENALEX_API_BASE}/works?filter=ids.openalex:{ids_filter}&per_page={len(batch_ids)}"

        result = await _make_request(session, url)

        batch_results = []
        if result and "results" in result:
            for work_data in result["results"]:
                work_data["abstract"] = _decode_abstract(work_data.get("abstract_inverted_index"))
                batch_results.append(work_data)
        return batch_results

    # Create batches and fetch concurrently
    batches = [referenced_ids[i:i + batch_size] for i in range(0, len(referenced_ids), batch_size)]
    batch_results = await asyncio.gather(*[fetch_batch(batch) for batch in batches])

    for batch_result in batch_results:
        references.extend(batch_result)

    if verbose and references:
        logger.debug("Successfully fetched reference details", count=len(references), openalex_id=openalex_id)

    return references


async def get_citations(
    session: aiohttp.ClientSession,
    openalex_id: str,
    limit: int = 100,
    verbose: bool = True
) -> list[dict[str, Any]]:
    """Get papers that cite this paper (forward links / citations).
    
    Uses the 'cites' filter to find works that cite the given paper.
    
    Args:
        session: aiohttp ClientSession
        openalex_id: OpenAlex work ID
        limit: Maximum number of citations to return
        verbose: Whether to print debug information
        
    Returns:
        List of citing work metadata dictionaries
    """
    # Ensure proper format
    if not openalex_id.startswith("W"):
        openalex_id = f"W{openalex_id}"

    url = f"{OPENALEX_API_BASE}/works?filter=cites:{openalex_id}&per_page={limit}&sort=cited_by_count:desc"

    result = await _make_request(session, url)

    citations = []
    if result:
        meta = result.get("meta", {})
        total_count = meta.get("count", 0)
        if verbose:
            logger.debug("OpenAlex citation count", openalex_id=openalex_id, total_count=total_count)

        if "results" in result:
            for work_data in result["results"]:
                # Decode abstract
                work_data["abstract"] = _decode_abstract(work_data.get("abstract_inverted_index"))
                citations.append(work_data)

    return citations


async def search_related_works(
    session: aiohttp.ClientSession,
    query: str,
    limit: int = 50,
    min_citations: int = 0,
    verbose: bool = True
) -> list[dict[str, Any]]:
    """Search for related works by keyword query.
    
    Useful as a fallback when seed papers have no indexed references/citations.
    Filters to papers with at least min_citations to get established works.
    
    Args:
        session: aiohttp ClientSession
        query: Search query string
        limit: Maximum number of results
        min_citations: Minimum citation count filter
        verbose: Whether to print debug information
        
    Returns:
        List of work metadata dictionaries
    """
    encoded_query = urllib.parse.quote(query)
    filter_part = ""
    if isinstance(min_citations, int) and min_citations > 0:
        filter_part = f"filter=cited_by_count:>{min_citations}&"

    url = (
        f"{OPENALEX_API_BASE}/works?"
        f"search={encoded_query}&"
        f"{filter_part}"
        f"sort=cited_by_count:desc&"
        f"per_page={limit}"
    )

    if verbose:
        logger.debug("Searching OpenAlex", query=query, min_citations=min_citations)

    result = await _make_request(session, url)

    works = []
    if result:
        meta = result.get("meta", {})
        total_count = meta.get("count", 0)
        if verbose:
            logger.debug(
                "OpenAlex search results",
                query=query,
                total_count=total_count,
                returning=min(limit, total_count)
            )

        if "results" in result:
            for work_data in result["results"]:
                work_data["abstract"] = _decode_abstract(work_data.get("abstract_inverted_index"))
                works.append(work_data)

    return works


async def search_papers(
    session: aiohttp.ClientSession,
    queries: list[str],
    num_results_per_query: int = 10,
    min_citations: int = 0,
) -> list[dict[str, Any]]:
    """Search OpenAlex for papers matching multiple queries concurrently.
    
    This is the main entry point for using OpenAlex as a seeding source.
    Returns results in a format compatible with the filter stage.
    
    Args:
        session: aiohttp ClientSession
        queries: List of search query strings
        num_results_per_query: Maximum number of results per query
        min_citations: Minimum citation count filter (helps quality)
        
    Returns:
        List of paper dicts with keys: id, title, abstract, publication_year,
        cited_by_count, source_query, and the original OpenAlex URL
    """
    async def search_single_query(query: str) -> list[dict[str, Any]]:
        """Search for a single query and tag results with source_query."""
        works = await search_related_works(
            session, 
            query, 
            limit=num_results_per_query,
            min_citations=min_citations,
            verbose=False
        )
        
        # Tag each result with the source query
        for work in works:
            work["source_query"] = query
        
        return works
    
    # Search all queries concurrently
    tasks = [search_single_query(q) for q in queries]
    results_per_query = await asyncio.gather(*tasks)
    
    # Flatten results
    all_results: list[dict[str, Any]] = []
    for results in results_per_query:
        all_results.extend(results)
    
    logger.debug(
        "OpenAlex search complete",
        num_queries=len(queries),
        total_results=len(all_results)
    )
    
    return all_results


async def get_work_with_refs_check(
    session: aiohttp.ClientSession,
    openalex_id: str
) -> tuple[dict[str, Any] | None, bool]:
    """Get work details and check if it has indexed references.
    
    Args:
        session: aiohttp ClientSession
        openalex_id: OpenAlex work ID
        
    Returns:
        Tuple of (work_data, has_references)
    """
    work = await get_work_details(session, openalex_id)
    if not work:
        return None, False

    has_refs = bool(work.get("referenced_works", []))
    return work, has_refs


# =============================================================================
# SEMANTIC SCHOLAR FALLBACK
# Used when OpenAlex doesn't have references indexed for new papers
# =============================================================================


async def _get_semantic_scholar_paper(
    session: aiohttp.ClientSession,
    arxiv_id: str
) -> dict[str, Any] | None:
    """Fetch paper details from Semantic Scholar using arXiv ID.
    
    Args:
        session: aiohttp ClientSession
        arxiv_id: arXiv ID (e.g., "2301.12345")
        
    Returns:
        Paper data dict or None
    """
    # Clean the arXiv ID
    arxiv_id = extract_arxiv_id(arxiv_id) or arxiv_id

    url = (f"{SEMANTIC_SCHOLAR_API_BASE}/paper/arXiv:{arxiv_id}"
           f"?fields=paperId,title,abstract,year,citationCount,references.paperId,"
           f"references.title,references.abstract,references.year,references.citationCount")

    semaphore = _get_s2_semaphore()

    async with semaphore:
        await asyncio.sleep(SEMANTIC_SCHOLAR_RATE_LIMIT_DELAY)

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 404 or response.status == 429 or response.status >= 400:
                    return None

                return await response.json()
        except Exception:
            return None


async def get_references_from_semantic_scholar(
    session: aiohttp.ClientSession,
    arxiv_id: str,
    limit: int = 100,
    verbose: bool = True
) -> list[dict[str, Any]]:
    """Get references from Semantic Scholar as fallback.
    
    Used when OpenAlex doesn't have references indexed for new papers.
    
    Args:
        session: aiohttp ClientSession
        arxiv_id: arXiv ID of the paper
        limit: Maximum number of references to return
        verbose: Whether to print debug information
        
    Returns:
        List of reference paper dicts (OpenAlex-compatible format)
    """
    if verbose:
        logger.debug("Trying Semantic Scholar", arxiv_id=arxiv_id)

    paper = await _get_semantic_scholar_paper(session, arxiv_id)
    if not paper:
        if verbose:
            logger.debug("Paper not found in Semantic Scholar", arxiv_id=arxiv_id)
        return []

    references_raw = paper.get("references", [])
    if not references_raw:
        if verbose:
            logger.debug("No references found in Semantic Scholar", arxiv_id=arxiv_id)
        return []

    if verbose:
        logger.debug("Found references in Semantic Scholar", arxiv_id=arxiv_id, count=len(references_raw))

    # Convert to OpenAlex-compatible format
    references = []
    for ref in references_raw[:limit]:
        if not ref.get("paperId"):
            continue

        ref_data = {
            "id": f"S2:{ref['paperId']}",  # Mark as S2 ID
            "title": ref.get("title"),
            "abstract": ref.get("abstract"),
            "publication_year": ref.get("year"),
            "cited_by_count": ref.get("citationCount", 0),
            "_source": "semantic_scholar"
        }
        references.append(ref_data)

    return references


async def get_references_with_fallback(
    session: aiohttp.ClientSession,
    openalex_id: str,
    arxiv_id: str | None = None,
    limit: int = 100,
    verbose: bool = True
) -> list[dict[str, Any]]:
    """Get references, falling back to Semantic Scholar if OpenAlex is empty.
    
    This is useful for new papers where OpenAlex hasn't indexed references yet.
    
    Args:
        session: aiohttp ClientSession
        openalex_id: OpenAlex work ID
        arxiv_id: Optional arXiv ID for fallback
        limit: Maximum number of references to return
        verbose: Whether to print debug information
        
    Returns:
        List of reference paper dicts
    """
    # Try OpenAlex first
    refs = await get_references(session, openalex_id, limit=limit, verbose=verbose)

    if refs:
        return refs

    # Fallback to Semantic Scholar if arXiv ID is available
    if arxiv_id:
        return await get_references_from_semantic_scholar(session, arxiv_id, limit=limit, verbose=verbose)

    return []


# =============================================================================
# BATCH OPERATIONS FOR CONCURRENT PROCESSING
# =============================================================================


async def batch_resolve_arxiv(
    session: aiohttp.ClientSession,
    arxiv_links: list[str]
) -> list[str | None]:
    """Resolve multiple arXiv links to OpenAlex IDs concurrently.
    
    Args:
        session: aiohttp ClientSession
        arxiv_links: List of arXiv links or IDs
        
    Returns:
        List of OpenAlex IDs (None for failed resolutions)
    """
    tasks = [resolve_arxiv_to_openalex(session, link) for link in arxiv_links]
    return await asyncio.gather(*tasks)


async def batch_get_references(
    session: aiohttp.ClientSession,
    openalex_ids: list[str],
    limit: int = 100,
    verbose: bool = False
) -> list[list[dict[str, Any]]]:
    """Get references for multiple papers concurrently.
    
    Args:
        session: aiohttp ClientSession
        openalex_ids: List of OpenAlex work IDs
        limit: Maximum number of references per paper
        verbose: Whether to print debug information
        
    Returns:
        List of reference lists (one per input paper)
    """
    tasks = [get_references(session, oid, limit=limit, verbose=verbose) for oid in openalex_ids]
    return await asyncio.gather(*tasks)


async def batch_get_citations(
    session: aiohttp.ClientSession,
    openalex_ids: list[str],
    limit: int = 100,
    verbose: bool = False
) -> list[list[dict[str, Any]]]:
    """Get citations for multiple papers concurrently.
    
    Args:
        session: aiohttp ClientSession
        openalex_ids: List of OpenAlex work IDs
        limit: Maximum number of citations per paper
        verbose: Whether to print debug information
        
    Returns:
        List of citation lists (one per input paper)
    """
    tasks = [get_citations(session, oid, limit=limit, verbose=verbose) for oid in openalex_ids]
    return await asyncio.gather(*tasks)


def create_session() -> aiohttp.ClientSession:
    """Create an aiohttp ClientSession with proper headers.
    
    Returns:
        Configured aiohttp ClientSession
    """
    headers = _build_headers()
    return aiohttp.ClientSession(headers=headers)
