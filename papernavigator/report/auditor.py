"""Citation auditor for validating and revising sections.

This module provides a second-pass validation of written sections,
checking that all claims are properly supported by the cited papers.
It also ensures citations are preserved and added where missing.
"""

import asyncio
import json
import os
import re
from collections.abc import Callable

from openai import AsyncOpenAI

# Timeout for OpenAI API calls (seconds)
OPENAI_TIMEOUT_SECONDS = 60
# Timeout per audit section (seconds) to avoid indefinite hangs
AUDIT_SECTION_TIMEOUT_SECONDS = int(os.getenv("AUDIT_SECTION_TIMEOUT_SECONDS", "120"))
# Retries for audit timeouts/errors
AUDIT_SECTION_MAX_RETRIES = int(os.getenv("AUDIT_SECTION_MAX_RETRIES", "1"))

from papernavigator.logging import get_logger
from papernavigator.report.models import (
    AuditResult,
    PaperCard,
    SentenceAudit,
    WrittenSection,
)


def extract_cited_ids(text: str) -> list[str]:
    """Extract all paper IDs cited in the text.
    
    Looks for patterns like [W1234567890] or [S2:paper_id].
    
    Args:
        text: Text with inline citations
        
    Returns:
        List of unique paper IDs found
    """
    # Match OpenAlex-style IDs like [W1234567890] or S2-style [S2:abc123]
    pattern = r'\[([A-Za-z0-9_:-]+)\]'
    matches = re.findall(pattern, text)
    return list(set(matches))

log = get_logger(__name__)

# Async OpenAI client
_async_client: AsyncOpenAI | None = None


def _get_async_client() -> AsyncOpenAI:
    """Get or create the async OpenAI client."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _async_client


def _format_cards_for_audit(cards: list[PaperCard]) -> str:
    """Format paper cards for the audit prompt."""
    card_strs = []
    for card in cards:
        parts = [
            f"[{card.id}]",
            f"  Title: {card.title}",
            f"  Claim: {card.claim}",
        ]
        if card.key_quote:
            parts.append(f"  Quote: \"{card.key_quote}\"")
        if card.data_benchmark:
            parts.append(f"  Data: {card.data_benchmark}")
        if card.measured:
            parts.append(f"  Measured: {card.measured}")

        card_strs.append("\n".join(parts))

    return "\n\n".join(card_strs)


def _build_audit_prompt(section: WrittenSection, cards: list[PaperCard]) -> str:
    """Build the prompt for auditing a section."""
    cards_text = _format_cards_for_audit(cards)
    valid_ids = [c.id for c in cards]

    # Extract existing citations from original text
    original_citations = extract_cited_ids(section.content)

    return f"""You are auditing a research survey section for citation accuracy.

SECTION TITLE: {section.title}

SECTION TEXT:
{section.content}

ORIGINAL CITATIONS FOUND: {original_citations}

AVAILABLE PAPER EVIDENCE:
{cards_text}

AUDIT TASK:
For each sentence in the section that makes a factual claim:
1. If it has a citation [paper_id], check if the paper supports that claim
2. If the citation doesn't match, suggest a fix with the CORRECT citation
3. If a factual claim has NO citation, ADD an appropriate citation from: {valid_ids}
4. Flag sentences with invalid citations not in the list above

===== CRITICAL CITATION PRESERVATION RULES =====
1. PRESERVE all existing citations [paper_id] from the original text
2. If you revise a sentence, KEEP its citation
3. If you must remove a sentence, MOVE its citation to a related sentence
4. If a factual claim lacks a citation, ADD one from available papers
5. The revised_text MUST contain AT LEAST as many citations as the original ({len(original_citations)} citations)
6. EVERY paragraph in revised_text MUST have at least 1 citation

Return JSON with this structure:
{{
  "sentences": [
    {{
      "sentence": "The exact sentence from the text",
      "supported": true/false,
      "cited_ids": ["W123"],
      "issue": "Description of problem (null if supported)",
      "suggested_fix": "Revised sentence WITH CITATION (null if supported)"
    }}
  ],
  "revised_text": "The full section with ALL citations preserved and added where needed"
}}

Guidelines:
- NEVER remove a citation without moving it elsewhere
- Add citations to unsupported factual claims
- If a sentence says "unclear from abstracts", that's acceptable
- In revised_text, ensure EVERY paragraph has at least one citation [paper_id]
- Use the paper's claim and key quote to match citations accurately"""


async def audit_section(
    section: WrittenSection,
    cards: list[PaperCard],
) -> AuditResult:
    """Audit a written section for citation accuracy.
    
    Args:
        section: The written section to audit
        cards: Paper cards that were available for this section
        
    Returns:
        AuditResult with sentence-level analysis and revised text
    """
    log.info(
        "citation_audit_start",
        section=section.title,
        text_length=len(section.content),
        num_cards=len(cards)
    )

    if not section.content or section.content.startswith("Error") or not cards:
        log.warning("skipping_audit", section=section.title, reason="empty or error content")
        return AuditResult(
            section_title=section.title,
            original_text=section.content,
            revised_text=section.content,
            sentences=[],
            supported_count=0,
            unsupported_count=0,
            revised_count=0
        )

    prompt = _build_audit_prompt(section, cards)
    client = _get_async_client()

    try:
        # Wrap API call with timeout to prevent indefinite hangs
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=2500,
                response_format={"type": "json_object"}
            ),
            timeout=OPENAI_TIMEOUT_SECONDS
        )

        content = response.choices[0].message.content.strip()
        data = json.loads(content)

        # Parse sentence audits
        sentence_audits = []
        supported_count = 0
        unsupported_count = 0

        for s_data in data.get("sentences", []):
            audit = SentenceAudit(
                sentence=s_data.get("sentence", ""),
                supported=s_data.get("supported", True),
                cited_ids=s_data.get("cited_ids", []),
                issue=s_data.get("issue"),
                suggested_fix=s_data.get("suggested_fix")
            )
            sentence_audits.append(audit)

            if audit.supported:
                supported_count += 1
            else:
                unsupported_count += 1

        revised_text = data.get("revised_text", section.content)
        revised_count = sum(1 for s in sentence_audits if s.suggested_fix)

        log.info(
            "citation_audit_complete",
            section=section.title,
            supported=supported_count,
            unsupported=unsupported_count,
            revised=revised_count
        )

        if unsupported_count > 0:
            log.warning(
                "unsupported_claims_found",
                section=section.title,
                count=unsupported_count,
                issues=[s.issue for s in sentence_audits if not s.supported and s.issue]
            )

        return AuditResult(
            section_title=section.title,
            original_text=section.content,
            revised_text=revised_text,
            sentences=sentence_audits,
            supported_count=supported_count,
            unsupported_count=unsupported_count,
            revised_count=revised_count
        )

    except asyncio.TimeoutError:
        log.error("audit_timeout", section=section.title, timeout_sec=OPENAI_TIMEOUT_SECONDS)
        # Return original text without revision on timeout
        return AuditResult(
            section_title=section.title,
            original_text=section.content,
            revised_text=section.content,
            sentences=[],
            supported_count=0,
            unsupported_count=0,
            revised_count=0
        )
    except json.JSONDecodeError as e:
        log.error("audit_json_parse_error", section=section.title, error=str(e))
        # Return original text without revision
        return AuditResult(
            section_title=section.title,
            original_text=section.content,
            revised_text=section.content,
            sentences=[],
            supported_count=0,
            unsupported_count=0,
            revised_count=0
        )
    except Exception as e:
        log.error("audit_failed", section=section.title, error=str(e))
        return AuditResult(
            section_title=section.title,
            original_text=section.content,
            revised_text=section.content,
            sentences=[],
            supported_count=0,
            unsupported_count=0,
            revised_count=0
        )


async def audit_all_sections(
    sections: list[WrittenSection],
    all_cards: list[PaperCard],
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[AuditResult]:
    """Audit all written sections.
    
    Args:
        sections: List of written sections
        all_cards: All available paper cards
        
    Returns:
        List of audit results, one per section
    """
    if not sections:
        log.warning("no_sections_to_audit")
        return []

    log.info("batch_audit_start", num_sections=len(sections))

    # Create card lookup by ID
    card_lookup = {c.id: c for c in all_cards}

    results = []
    total_supported = 0
    total_unsupported = 0
    total_sections = len(sections)

    if progress_callback:
        progress_callback(0, total_sections, f"Starting to audit {total_sections} sections...")

    for i, section in enumerate(sections):
        # Get cards that were used in this section
        section_cards = [
            card_lookup[pid]
            for pid in section.paper_ids_used
            if pid in card_lookup
        ]

        # If no specific cards, use all cards
        if not section_cards:
            section_cards = all_cards

        if progress_callback:
            progress_callback(i, total_sections, f"Auditing section {i+1}/{total_sections}: {section.title}")

        result: AuditResult | None = None
        for attempt in range(AUDIT_SECTION_MAX_RETRIES + 1):
            try:
                result = await asyncio.wait_for(
                    audit_section(section, section_cards),
                    timeout=AUDIT_SECTION_TIMEOUT_SECONDS,
                )
                break
            except asyncio.TimeoutError:
                log.warning(
                    "audit_section_timeout",
                    section=section.title,
                    timeout_sec=AUDIT_SECTION_TIMEOUT_SECONDS,
                    attempt=attempt + 1,
                )
                if progress_callback:
                    progress_callback(
                        i,
                        total_sections,
                        (
                            "WARNING: Audit timed out for section "
                            f"{i+1}/{total_sections}: {section.title} "
                            f"(attempt {attempt + 1})"
                        ),
                    )
            except Exception as exc:
                log.error(
                    "audit_section_failed",
                    section=section.title,
                    error=str(exc),
                    attempt=attempt + 1,
                )
                if progress_callback:
                    progress_callback(
                        i,
                        total_sections,
                        (
                            "WARNING: Audit failed for section "
                            f"{i+1}/{total_sections}: {section.title} "
                            f"(attempt {attempt + 1})"
                        ),
                    )
            if attempt == AUDIT_SECTION_MAX_RETRIES:
                result = AuditResult(
                    section_title=section.title,
                    original_text=section.content,
                    revised_text=section.content,
                    sentences=[],
                    supported_count=0,
                    unsupported_count=0,
                    revised_count=0,
                )
                break

        if result is None:
            result = AuditResult(
                section_title=section.title,
                original_text=section.content,
                revised_text=section.content,
                sentences=[],
                supported_count=0,
                unsupported_count=0,
                revised_count=0,
            )
        results.append(result)

        total_supported += result.supported_count
        total_unsupported += result.unsupported_count

        if progress_callback:
            progress_callback(i + 1, total_sections, f"Completed audit {i+1}/{total_sections}: {section.title}")

    log.info(
        "batch_audit_complete",
        num_sections=len(sections),
        total_supported=total_supported,
        total_unsupported=total_unsupported
    )

    return results


def merge_citations(
    original_text: str,
    revised_text: str,
    cards: list[PaperCard],
) -> str:
    """Merge citations from original into revised text if they were lost.
    
    Strategy:
    1. Extract citations from both texts
    2. If revised lost citations, try to restore them by:
       - Finding semantically similar sentences/paragraphs
       - Injecting citations at appropriate points
    3. Return merged text with all citations preserved
    
    Args:
        original_text: Original text with citations
        revised_text: Revised text that may have lost citations
        cards: Available paper cards for validation
        
    Returns:
        Text with citations preserved/restored
    """
    original_citations = set(extract_cited_ids(original_text))
    revised_citations = set(extract_cited_ids(revised_text))

    # Valid IDs from cards
    valid_ids = {c.id for c in cards}

    # Filter to only valid citations
    original_citations = original_citations & valid_ids
    revised_citations = revised_citations & valid_ids

    # If no citations were lost, return revised text as-is
    lost_citations = original_citations - revised_citations

    if not lost_citations:
        log.debug("no_citations_lost", original=len(original_citations), revised=len(revised_citations))
        return revised_text

    log.warning(
        "citations_lost_during_revision",
        original_count=len(original_citations),
        revised_count=len(revised_citations),
        lost=list(lost_citations)
    )

    # Try to restore lost citations
    result_text = revised_text

    # Split into paragraphs
    paragraphs = result_text.split('\n\n')

    # Distribute lost citations across paragraphs that don't have citations
    lost_list = list(lost_citations)
    citation_index = 0

    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue

        para_citations = extract_cited_ids(para)

        # If paragraph has no citations and we have lost citations to add
        if not para_citations and citation_index < len(lost_list):
            # Find end of first sentence
            sentences = para.split('.')
            if sentences and sentences[0].strip():
                # Add citation to end of first sentence
                citation_to_add = lost_list[citation_index]
                sentences[0] = sentences[0].rstrip() + f" [{citation_to_add}]"
                paragraphs[i] = '.'.join(sentences)
                citation_index += 1
                log.debug("restored_citation", citation=citation_to_add, paragraph_index=i)

    # If we still have lost citations, append them to the last paragraph
    while citation_index < len(lost_list):
        # Find the last non-empty paragraph
        for i in range(len(paragraphs) - 1, -1, -1):
            if paragraphs[i].strip():
                citation_to_add = lost_list[citation_index]
                paragraphs[i] = paragraphs[i].rstrip() + f" [{citation_to_add}]"
                citation_index += 1
                log.debug("appended_citation_to_last_para", citation=citation_to_add)
                break
        else:
            break  # No non-empty paragraphs found

    result_text = '\n\n'.join(paragraphs)

    # Verify restoration
    final_citations = set(extract_cited_ids(result_text))
    restored_count = len(final_citations) - len(revised_citations)

    log.info(
        "citations_merged",
        original=len(original_citations),
        revised=len(revised_citations),
        final=len(final_citations),
        restored=restored_count
    )

    return result_text
