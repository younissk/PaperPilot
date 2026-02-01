"""arXiv API search functionality (Async version).

This module provides async functions to search arXiv for academic papers
with support for concurrent batch searches.
"""

import asyncio
import urllib.parse
import xml.etree.ElementTree as ET

import aiohttp

from papernavigator.async_utils import get_loop_semaphore, validate_loop
from papernavigator.models import ArxivEntry, ArxivFeed, Author, Category, Link

# arXiv rate limiting - be respectful of their API
ARXIV_MAX_CONCURRENT = 3
ARXIV_RATE_LIMIT_DELAY = 0.5  # 500ms between requests


def _parse_arxiv_response(data: bytes) -> ArxivFeed:
    """Parse arXiv API XML response into ArxivFeed model.
    
    Args:
        data: Raw XML bytes from arXiv API
        
    Returns:
        Parsed ArxivFeed object
    """
    # Define namespaces used in arXiv Atom feed
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }

    root = ET.fromstring(data)

    # Extract entries first
    entries = []
    for entry in root.findall('atom:entry', ns):
        # Authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            auth_info = {'name': name_elem.text if name_elem is not None else "Unknown"}
            affil = author.find('arxiv:affiliation', ns)
            if affil is not None:
                auth_info['affiliation'] = affil.text
            authors.append(Author(**auth_info))

        # Categories
        categories = [
            Category(term=cat.get('term'), scheme=cat.get('scheme'))
            for cat in entry.findall('atom:category', ns)
        ]

        # Links
        links = [
            Link(
                href=link.get('href'),
                rel=link.get('rel'),
                type=link.get('type'),
                title=link.get('title')
            )
            for link in entry.findall('atom:link', ns)
        ]

        # ArXiv specific extensions
        arxiv_fields = {}
        for field in ['comment', 'journal_ref', 'doi']:
            val = entry.find(f'arxiv:{field}', ns)
            if val is not None:
                arxiv_fields[field] = val.text

        primary_cat = entry.find('arxiv:primary_category', ns)
        if primary_cat is not None:
            arxiv_fields['primary_category'] = primary_cat.get('term')

        id_elem = entry.find('atom:id', ns)
        title_elem = entry.find('atom:title', ns)
        updated_elem = entry.find('atom:updated', ns)
        published_elem = entry.find('atom:published', ns)
        summary_elem = entry.find('atom:summary', ns)

        entries.append(ArxivEntry(
            id=id_elem.text if id_elem is not None else "",
            title=title_elem.text.strip().replace('\n', ' ') if title_elem is not None and title_elem.text else "",
            updated=updated_elem.text if updated_elem is not None else "",
            published=published_elem.text if published_elem is not None else "",
            summary=summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None and summary_elem.text else "",
            authors=authors,
            links=links,
            categories=categories,
            **arxiv_fields
        ))

    # Construct final feed
    id_elem = root.find('atom:id', ns)
    title_elem = root.find('atom:title', ns)
    updated_elem = root.find('atom:updated', ns)
    total_elem = root.find('opensearch:totalResults', ns)
    start_elem = root.find('opensearch:startIndex', ns)
    items_elem = root.find('opensearch:itemsPerPage', ns)

    feed_data = ArxivFeed(
        id=id_elem.text if id_elem is not None else "",
        title=title_elem.text if title_elem is not None else "",
        updated=updated_elem.text if updated_elem is not None else "",
        totalResults=int(total_elem.text) if total_elem is not None else 0,
        startIndex=int(start_elem.text) if start_elem is not None else 0,
        itemsPerPage=int(items_elem.text) if items_elem is not None else 0,
        entries=entries
    )

    return feed_data


async def search_articles(
    session: aiohttp.ClientSession,
    query: str,
    max_results: int = 10
) -> ArxivFeed:
    """Search arXiv for articles matching the query.
    
    Args:
        session: aiohttp ClientSession
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        ArxivFeed containing search results
    """
    encoded_query = urllib.parse.quote(query)
    url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}'

    semaphore = get_loop_semaphore("arxiv", ARXIV_MAX_CONCURRENT)
    validate_loop(semaphore, "arxiv_semaphore")

    async with semaphore:
        await asyncio.sleep(ARXIV_RATE_LIMIT_DELAY)

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.read()
                return _parse_arxiv_response(data)
        except Exception:
            # Return empty feed on error
            return ArxivFeed(
                id="",
                title="",
                updated="",
                totalResults=0,
                startIndex=0,
                itemsPerPage=0,
                entries=[]
            )


async def search_all_queries(
    session: aiohttp.ClientSession,
    queries: list[str],
    max_results_per_query: int = 10
) -> list[ArxivFeed]:
    """Search arXiv for multiple queries concurrently.
    
    Args:
        session: aiohttp ClientSession
        queries: List of search query strings
        max_results_per_query: Maximum number of results per query
        
    Returns:
        List of ArxivFeed objects, one per query
    """
    tasks = [
        search_articles(session, query, max_results_per_query)
        for query in queries
    ]
    return await asyncio.gather(*tasks)
