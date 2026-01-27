"""Section writing with enforced citations.

This module writes report sections using LLM with strict citation
enforcement to prevent hallucinations and ensure traceability.
"""

import os
import re
from collections.abc import Callable

from openai import AsyncOpenAI

from paperpilot.core.logging import get_logger
from paperpilot.core.report.models import PaperCard, SectionPlan, WrittenSection

log = get_logger(__name__)

# Async OpenAI client
_async_client: AsyncOpenAI | None = None


def _get_async_client() -> AsyncOpenAI:
    """Get or create the async OpenAI client."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _async_client


def _format_cards_for_prompt(cards: list[PaperCard]) -> str:
    """Format paper cards for inclusion in the LLM prompt."""
    card_strs = []
    for card in cards:
        parts = [
            f"[{card.id}] {card.title}",
            f"  Claim: {card.claim}",
        ]
        if card.data_benchmark:
            parts.append(f"  Data/Benchmark: {card.data_benchmark}")
        if card.measured:
            parts.append(f"  Measured: {card.measured}")
        if card.limitation:
            parts.append(f"  Limitation: {card.limitation}")
        if card.key_quote:
            parts.append(f"  Key Quote: \"{card.key_quote}\"")

        card_strs.append("\n".join(parts))

    return "\n\n".join(card_strs)


def _build_section_prompt(section: SectionPlan, cards: list[PaperCard]) -> str:
    """Build the prompt for writing a section."""
    cards_text = _format_cards_for_prompt(cards)
    bullets = "\n".join([f"- {b}" for b in section.bullet_claims])
    valid_ids = ", ".join([c.id for c in cards])

    # Get example IDs for the prompt
    example_ids = [c.id for c in cards[:2]] if len(cards) >= 2 else [c.id for c in cards]

    return f"""You are writing a section for a research survey report. 

SECTION TITLE: {section.title}

TOPICS TO COVER:
{bullets}

AVAILABLE PAPERS (use ONLY these for citations):
{cards_text}

===== CITATION EXAMPLES =====

GOOD EXAMPLE (FOLLOW THIS):
"LLMs have demonstrated significant potential in recommendation tasks [{example_ids[0] if example_ids else 'paper_id'}]. Building on this, recent frameworks combine user history with language models to improve personalization [{example_ids[1] if len(example_ids) > 1 else example_ids[0] if example_ids else 'paper_id'}]."

BAD EXAMPLE (DO NOT DO THIS - NO CITATIONS):
"LLMs have demonstrated significant potential in recommendation tasks. Building on this, recent frameworks combine user history with language models."

===== STRICT CITATION RULES =====
1. EVERY paragraph MUST contain at least 1 citation in format [paper_id]
2. EVERY factual claim about a paper MUST have a citation immediately after it
3. Citations MUST come ONLY from these IDs: {valid_ids}
4. If you cannot find evidence for a claim, write: "This aspect remains unclear from available abstracts."
5. Do NOT make up citations or use IDs not in the list above
6. Use the paper's claim and key quote to accurately represent what each paper contributes

Write 2-4 paragraphs covering the topics above. Each paragraph MUST:
- Make a clear point about the research theme
- Include AT LEAST ONE citation [paper_id] per paragraph
- Support claims with specific citations immediately after the claim
- Be concise and academic in tone

CRITICAL: Every paragraph MUST have at least one citation. Follow the GOOD EXAMPLE format.

Return ONLY the section content (no title, no JSON wrapper)."""


def extract_cited_ids(text: str) -> list[str]:
    """Extract all paper IDs cited in the text.
    
    Looks for patterns like [W1234567890] or [S2:paper_id].
    
    Args:
        text: Text with inline citations
        
    Returns:
        List of unique paper IDs found
    """
    # Match OpenAlex-style IDs [W1234567890] or S2-style [S2:abc123def]
    pattern = r'\[([A-Za-z0-9_:-]+)\]'
    matches = re.findall(pattern, text)
    return list(set(matches))


async def write_section(
    section: SectionPlan,
    cards: list[PaperCard],
) -> WrittenSection:
    """Write a single section with enforced citations.
    
    Args:
        section: The section plan with title and bullet claims
        cards: Paper cards relevant to this section
        
    Returns:
        WrittenSection with content and cited paper IDs
    """
    log.info(
        "section_writing_start",
        section=section.title,
        num_cards=len(cards),
        planned_ids=len(section.relevant_paper_ids)
    )

    if not cards:
        log.warning("no_cards_for_section", section=section.title)
        return WrittenSection(
            title=section.title,
            content="No papers available for this section.",
            paper_ids_used=[]
        )

    prompt = _build_section_prompt(section, cards)
    client = _get_async_client()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low temperature for factual accuracy
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        cited_ids = extract_cited_ids(content)

        # Validate cited IDs against available cards
        valid_ids = {c.id for c in cards}
        invalid_ids = [cid for cid in cited_ids if cid not in valid_ids]

        if invalid_ids:
            log.warning(
                "invalid_citations_found",
                section=section.title,
                invalid_ids=invalid_ids
            )

        valid_cited = [cid for cid in cited_ids if cid in valid_ids]
        word_count = len(content.split())

        log.info(
            "section_writing_complete",
            section=section.title,
            word_count=word_count,
            citations=len(valid_cited)
        )

        # Check citation density
        if len(valid_cited) == 0 and cards:
            log.warning("low_citation_density", section=section.title, word_count=word_count)

        return WrittenSection(
            title=section.title,
            content=content,
            paper_ids_used=valid_cited
        )

    except Exception as e:
        log.error("section_writing_failed", section=section.title, error=str(e))
        return WrittenSection(
            title=section.title,
            content=f"Error generating section: {str(e)}",
            paper_ids_used=[]
        )


async def rewrite_with_strict_citations(
    section: WrittenSection,
    cards: list[PaperCard],
) -> WrittenSection:
    """Re-write section with strict citation enforcement.
    
    Uses a more aggressive prompt that requires citations in every paragraph.
    
    Args:
        section: Section to rewrite
        cards: Available paper cards
        
    Returns:
        Rewritten section with citations
    """
    log.info("rewriting_with_strict_citations", section=section.title)

    cards_text = _format_cards_for_prompt(cards)
    valid_ids = ", ".join([c.id for c in cards])

    prompt = f"""TASK: Rewrite this section to include proper citations.

ORIGINAL SECTION TITLE: {section.title}

ORIGINAL TEXT (missing citations):
{section.content}

AVAILABLE PAPERS (you MUST cite from these):
{cards_text}

REQUIREMENTS:
1. EVERY paragraph MUST have at least 1 citation [paper_id]
2. Keep the same content and meaning
3. Add citations [paper_id] after factual claims
4. Use ONLY these IDs: {valid_ids}

EXAMPLE OUTPUT FORMAT:
"Recent research has shown significant advances in this area [W1234567890]. Multiple approaches have been proposed to address this challenge [{cards[0].id if cards else 'paper_id'}]."

Return ONLY the rewritten text with citations. Do not include any explanation."""

    client = _get_async_client()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        cited_ids = extract_cited_ids(content)

        # Validate cited IDs
        valid_id_set = {c.id for c in cards}
        valid_cited = [cid for cid in cited_ids if cid in valid_id_set]

        log.info(
            "rewrite_complete",
            section=section.title,
            citations=len(valid_cited)
        )

        return WrittenSection(
            title=section.title,
            content=content,
            paper_ids_used=valid_cited
        )

    except Exception as e:
        log.error("rewrite_failed", section=section.title, error=str(e))
        return section  # Return original if rewrite fails


async def validate_and_rewrite_if_needed(
    section: WrittenSection,
    cards: list[PaperCard],
    min_citations_per_100_words: float = 1.0,
) -> WrittenSection:
    """Validate citation density and re-write if too low.
    
    Args:
        section: Written section to validate
        cards: Available paper cards
        min_citations_per_100_words: Minimum citation density threshold
        
    Returns:
        Section with adequate citations (re-written if needed)
    """
    citations = extract_cited_ids(section.content)
    words = len(section.content.split())
    density = len(citations) / (words / 100) if words > 0 else 0

    if density < min_citations_per_100_words:
        log.warning(
            "low_citation_density_rewriting",
            section=section.title,
            density=round(density, 2),
            target=min_citations_per_100_words,
            current_citations=len(citations),
            word_count=words
        )
        # Re-write with stronger enforcement
        return await rewrite_with_strict_citations(section, cards)

    log.debug(
        "citation_density_ok",
        section=section.title,
        density=round(density, 2)
    )
    return section


async def write_all_sections(
    outline_sections: list[SectionPlan],
    all_cards: list[PaperCard],
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[WrittenSection]:
    """Write all sections from the outline.
    
    Args:
        outline_sections: List of section plans from the outline
        all_cards: All available paper cards
        
    Returns:
        List of written sections
    """
    if not outline_sections:
        log.warning("no_sections_to_write")
        return []

    # Create a lookup for cards by ID
    card_lookup = {c.id: c for c in all_cards}

    # Write sections sequentially to maintain coherence
    # (Could parallelize if needed, but sections may reference each other)
    written_sections = []
    total_sections = len(outline_sections)

    if progress_callback:
        progress_callback(0, total_sections, f"Starting to write {total_sections} sections...")

    for i, section in enumerate(outline_sections):
        # Get cards for this section
        section_cards = [
            card_lookup[pid]
            for pid in section.relevant_paper_ids
            if pid in card_lookup
        ]

        # If no specific cards assigned, use all cards
        if not section_cards:
            section_cards = all_cards
            log.debug("using_all_cards_for_section", section=section.title)

        if progress_callback:
            progress_callback(i, total_sections, f"Writing section {i+1}/{total_sections}: {section.title}")

        written = await write_section(section, section_cards)

        # Validate and rewrite if citation density is too low
        written = await validate_and_rewrite_if_needed(written, section_cards)

        written_sections.append(written)

        if progress_callback:
            progress_callback(i + 1, total_sections, f"Completed section {i+1}/{total_sections}: {section.title}")

    return written_sections


async def write_introduction(query: str, cards: list[PaperCard]) -> str:
    """Write the introduction section.
    
    Args:
        query: Original research query
        cards: All paper cards
        
    Returns:
        Introduction text
    """
    log.info("writing_introduction", query=query, num_cards=len(cards))

    # Get a sample of claims for context
    claims = [f"- {c.claim} [{c.id}]" for c in cards[:10]]
    claims_text = "\n".join(claims)

    prompt = f"""Write a brief introduction (2-3 paragraphs) for a research survey on:

Query: {query}

Sample of papers covered (showing their main claims):
{claims_text}

The introduction should:
1. Introduce the research topic and its importance
2. Briefly outline what aspects the survey covers
3. Include 2-3 citations to key foundational papers [paper_id]

Write concise, academic prose. Return only the introduction text."""

    client = _get_async_client()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        log.info("introduction_complete", word_count=len(content.split()))
        return content

    except Exception as e:
        log.error("introduction_failed", error=str(e))
        return f"This report surveys research on: {query}"


async def write_conclusion(
    query: str,
    cards: list[PaperCard],
    sections: list[WrittenSection]
) -> str:
    """Write the conclusion section.
    
    Args:
        query: Original research query
        cards: All paper cards
        sections: Written sections for context
        
    Returns:
        Conclusion text
    """
    log.info("writing_conclusion", query=query, num_sections=len(sections))

    # Summarize sections
    section_summaries = "\n".join([
        f"- {s.title}: {len(s.paper_ids_used)} papers cited"
        for s in sections
    ])

    # Get limitations from cards
    limitations = [c.limitation for c in cards if c.limitation][:5]
    limitations_text = "\n".join([f"- {l}" for l in limitations]) if limitations else "No explicit limitations noted."

    prompt = f"""Write a brief conclusion (2 paragraphs) for a research survey on:

Query: {query}

Sections covered:
{section_summaries}

Key limitations mentioned in papers:
{limitations_text}

The conclusion should:
1. Summarize the main themes and findings
2. Note key open challenges or future directions
3. Be concise and forward-looking

Write academic prose. Return only the conclusion text (no citations needed in conclusion)."""

    client = _get_async_client()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        log.info("conclusion_complete", word_count=len(content.split()))
        return content

    except Exception as e:
        log.error("conclusion_failed", error=str(e))
        return f"This survey covered research on {query}. Further investigation is warranted."


def find_most_relevant_card(text: str, cards: list[PaperCard]) -> PaperCard | None:
    """Find most relevant card for a text snippet using keyword matching.
    
    Uses simple keyword overlap between text and card title/claim.
    
    Args:
        text: Text snippet to match
        cards: Available paper cards
        
    Returns:
        Most relevant PaperCard, or None if no match found
    """
    if not cards:
        return None

    text_lower = text.lower()
    text_words = set(text_lower.split())

    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
        'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'also',
        'this', 'that', 'these', 'those', 'which', 'who', 'whom', 'what',
    }
    text_words = text_words - stop_words

    best_match = None
    best_score = 0

    for card in cards:
        # Score based on keyword overlap
        title_words = set(card.title.lower().split()) - stop_words
        claim_words = set(card.claim.lower().split()) - stop_words

        title_overlap = len(title_words & text_words)
        claim_overlap = len(claim_words & text_words)

        # Weight title matches more heavily
        score = title_overlap * 2 + claim_overlap

        if score > best_score:
            best_score = score
            best_match = card

    return best_match if best_score > 0 else (cards[0] if cards else None)


def inject_citations_if_missing(
    text: str,
    cards: list[PaperCard],
    min_per_paragraph: int = 1,
) -> str:
    """Post-process text to inject citations where missing.
    
    Strategy:
    1. Split into paragraphs
    2. For each paragraph without citations:
       - Find most relevant card using keyword matching
       - Inject citation at end of first sentence
    3. Return text with citations injected
    
    Args:
        text: Section text
        cards: Available paper cards
        min_per_paragraph: Minimum citations per paragraph
        
    Returns:
        Text with citations injected
    """
    if not cards:
        return text

    paragraphs = text.split('\n\n')
    result_paragraphs = []
    injected_count = 0

    for para in paragraphs:
        if not para.strip():
            result_paragraphs.append(para)
            continue

        existing = extract_cited_ids(para)

        if len(existing) < min_per_paragraph:
            # Find most relevant card for this paragraph
            best_card = find_most_relevant_card(para, cards)

            if best_card and best_card.id not in existing:
                # Find end of first sentence and inject citation
                # Handle multiple sentence endings
                first_period = para.find('.')

                if first_period > 0:
                    # Insert citation before the period
                    para = para[:first_period] + f" [{best_card.id}]" + para[first_period:]
                    injected_count += 1
                    log.debug("injected_citation", card_id=best_card.id)
                else:
                    # No period found, append to end
                    para = para.rstrip() + f" [{best_card.id}]"
                    injected_count += 1

        result_paragraphs.append(para)

    if injected_count > 0:
        log.info("citations_injected", count=injected_count)

    return '\n\n'.join(result_paragraphs)
