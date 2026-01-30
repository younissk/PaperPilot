"""Report generator orchestrating the full pipeline.

This module coordinates the complete report generation process:
1. Load and select top-k papers
2. Generate paper cards
3. Create outline
4. Write sections with citations
5. Audit citations
6. Assemble final report
"""

import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from papernavigator.logging import get_logger
from papernavigator.report.auditor import audit_all_sections, merge_citations
from papernavigator.report.cards import generate_paper_cards
from papernavigator.report.models import (
    AuditResult,
    OpenProblem,
    PaperCard,
    Report,
    ResearchItem,
    WrittenSection,
)
from papernavigator.report.outline import generate_outline
from papernavigator.report.writer import (
    extract_cited_ids,
    inject_citations_if_missing,
    write_all_sections,
    write_conclusion,
    write_introduction,
)

log = get_logger(__name__)


def load_papers_from_file(file_path: Path) -> tuple[list[dict], str]:
    """Load papers from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Tuple of (papers list, query string)
    """
    log.debug("loading_papers", file=str(file_path))

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    query = data.get("query", "Unknown query")

    log.info("papers_loaded", file=str(file_path), count=len(papers))
    return papers, query


def select_top_k_papers(
    elo_file: Path | None,
    snowball_file: Path,
    k: int = 30,
) -> tuple[list[dict], str]:
    """Select top-k papers for report generation.
    
    Priority: elo_ranked.json > snowball.json
    
    Args:
        elo_file: Path to elo ranking file (optional)
        snowball_file: Path to snowball results file
        k: Number of top papers to select
        
    Returns:
        Tuple of (top-k papers, query string)
    """
    # Try elo-ranked first
    if elo_file and elo_file.exists():
        log.info("using_elo_ranked", file=str(elo_file), top_k=k)
        papers, query = load_papers_from_file(elo_file)
        # Sort by elo_rating descending
        papers = sorted(
            papers,
            key=lambda p: p.get("elo_rating", 0),
            reverse=True
        )
    elif snowball_file.exists():
        log.info("using_snowball_fallback", file=str(snowball_file), top_k=k)
        papers, query = load_papers_from_file(snowball_file)
        # Sort by citation_count descending
        papers = sorted(
            papers,
            key=lambda p: p.get("citation_count", 0),
            reverse=True
        )
    else:
        raise FileNotFoundError(
            f"Neither elo file nor snowball file found: {elo_file}, {snowball_file}"
        )

    selected = papers[:k]
    log.info(
        "papers_selected",
        total_available=len(papers),
        selected=len(selected),
        top_paper=selected[0].get("title", "Unknown")[:50] if selected else None
    )

    return selected, query




def _sections_to_research_items(
    audit_results: list[AuditResult],
    original_sections: list[WrittenSection],
    all_cards: list[PaperCard],
) -> list[ResearchItem]:
    """Convert audited sections to ResearchItem format with citation preservation.
    
    This function ensures citations are preserved through the audit process by:
    1. Merging citations from original text if they were lost
    2. Injecting citations into paragraphs that don't have any
    
    Args:
        audit_results: List of audit results for each section
        original_sections: Original written sections before audit
        all_cards: All available paper cards
        
    Returns:
        List of ResearchItem for the report
    """
    items = []

    for i, result in enumerate(audit_results):
        # Get original section (if available)
        original = original_sections[i] if i < len(original_sections) else None

        # Start with revised text
        final_text = result.revised_text

        # Merge citations from original if they were lost
        if original:
            final_text = merge_citations(original.content, final_text, all_cards)

        # Final injection pass to ensure every paragraph has citations
        final_text = inject_citations_if_missing(final_text, all_cards)

        # Extract final citations
        cited_ids = extract_cited_ids(final_text)

        log.debug(
            "section_to_research_item",
            section=result.section_title,
            citations=len(cited_ids)
        )

        items.append(ResearchItem(
            title=result.section_title,
            summary=final_text,
            paper_ids=cited_ids
        ))

    return items


def _extract_open_problems(cards: list[PaperCard]) -> list[OpenProblem]:
    """Extract open problems from paper limitations.
    
    Args:
        cards: Paper cards with potential limitations
        
    Returns:
        List of OpenProblem items
    """
    problems = []
    seen_limitations = set()

    for card in cards:
        if card.limitation and card.limitation not in seen_limitations:
            seen_limitations.add(card.limitation)
            problems.append(OpenProblem(
                title=f"Limitation from {card.title[:30]}...",
                text=card.limitation,
                paper_ids=[card.id]
            ))

    # Limit to top 5 problems
    return problems[:5]


async def generate_report(
    snowball_file: Path,
    elo_file: Path | None = None,
    top_k: int = 30,
    progress_callback: Callable[[int, str, int, int, str], None] | None = None,
) -> Report:
    """Generate a complete research report.
    
    This is the main entry point for report generation. It orchestrates
    the entire pipeline from loading papers to producing the final report.
    
    Args:
        snowball_file: Path to snowball results JSON
        elo_file: Optional path to elo ranking JSON (preferred source)
        top_k: Number of top papers to use
        
    Returns:
        Complete Report object
    """
    start_time = time.time()
    log.info("report_generation_start", snowball_file=str(snowball_file), top_k=top_k)

    # Step 0: Select top-k papers
    log.info("step_0_paper_selection")
    papers, query = select_top_k_papers(elo_file, snowball_file, k=top_k)

    if not papers:
        raise ValueError("No papers available for report generation")

    if progress_callback:
        progress_callback(0, "Selecting Top Papers", 1, 1, f"Selected {len(papers)} papers")

    # Step 1: Generate paper cards
    log.info("step_1_card_generation", num_papers=len(papers))
    cards = await generate_paper_cards(papers, progress_callback=lambda current, total, msg: (
        progress_callback(1, "Generating Paper Cards", current, total, msg) if progress_callback else None
    ))

    if not cards:
        raise ValueError("Failed to generate any paper cards")

    log.info("cards_ready", count=len(cards))

    if progress_callback:
        progress_callback(1, "Generating Paper Cards", len(cards), len(cards), f"Generated {len(cards)} paper cards")

    # Step 2: Generate outline
    log.info("step_2_outline_generation")
    outline = await generate_outline(query, cards)
    log.info("outline_ready", num_sections=len(outline.sections))

    if progress_callback:
        progress_callback(2, "Creating Report Outline", 1, 1, f"Created outline with {len(outline.sections)} sections")

    # Step 3: Write sections
    log.info("step_3_section_writing")
    written_sections = await write_all_sections(
        outline.sections,
        cards,
        progress_callback=lambda current, total, msg: (
            progress_callback(3, "Writing Sections", current, total, msg) if progress_callback else None
        )
    )
    log.info("sections_written", count=len(written_sections))

    if progress_callback:
        progress_callback(3, "Writing Sections", len(written_sections), len(written_sections), f"Wrote {len(written_sections)} sections")

    # Step 4: Audit sections
    log.info("step_4_citation_audit")
    audit_results = await audit_all_sections(
        written_sections,
        cards,
        progress_callback=lambda current, total, msg: (
            progress_callback(4, "Auditing Citations", current, total, msg) if progress_callback else None
        )
    )
    log.info("audit_complete", count=len(audit_results))

    if progress_callback:
        progress_callback(4, "Auditing Citations", len(audit_results), len(audit_results), f"Audited {len(audit_results)} sections")

    # Step 5: Write introduction and conclusion
    log.info("step_5_intro_conclusion")
    introduction = await write_introduction(query, cards)
    conclusion = await write_conclusion(query, cards, written_sections)

    if progress_callback:
        progress_callback(5, "Writing Introduction & Conclusion", 1, 1, "Completed introduction and conclusion")

    # Step 6: Assemble report with citation preservation
    log.info("step_6_assembly")

    current_research = _sections_to_research_items(
        audit_results,
        written_sections,
        cards
    )
    open_problems = _extract_open_problems(cards)

    report = Report(
        query=query,
        generated_at=datetime.now().isoformat(),
        total_papers_used=len(cards),
        introduction=introduction,
        current_research=current_research,
        open_problems=open_problems,
        conclusion=conclusion,
        paper_cards=cards,
    )

    if progress_callback:
        progress_callback(6, "Assembling Report", 1, 1, "Assembling final report")

    # Step 7: Final citation quality check
    log.info("step_7_final_check")
    report, warnings = final_citation_check(report)

    if progress_callback:
        progress_callback(7, "Final Quality Check", 1, 1, f"Quality check complete ({len(warnings)} warnings)")

    # Calculate statistics
    total_citations = sum(len(item.paper_ids) for item in current_research)
    duration = time.time() - start_time

    log.info(
        "report_generation_complete",
        query=query,
        sections=len(current_research),
        total_citations=total_citations,
        open_problems=len(open_problems),
        duration_sec=round(duration, 2),
        warnings=len(warnings)
    )

    return report


def final_citation_check(report: Report) -> tuple[Report, list[str]]:
    """Perform final validation of citation quality.
    
    Validates that each section has adequate citations and logs warnings
    for sections that don't meet minimum standards.
    
    Args:
        report: Report to validate
        
    Returns:
        Tuple of (report, list of warning messages)
    """
    warnings = []

    for item in report.current_research:
        citations = len(item.paper_ids)
        words = len(item.summary.split())
        density = citations / (words / 100) if words > 0 else 0

        if citations == 0:
            warnings.append(f"Section '{item.title}' has 0 citations")
        elif density < 0.5:
            warnings.append(
                f"Section '{item.title}' has low citation density: "
                f"{density:.2f} per 100 words ({citations} citations in {words} words)"
            )

    if warnings:
        log.warning(
            "final_citation_check_warnings",
            num_warnings=len(warnings),
            warnings=warnings
        )
    else:
        log.info("final_citation_check_passed", sections=len(report.current_research))

    return report, warnings


def report_to_dict(report: Report) -> dict:
    """Convert a Report to a JSON-serializable dictionary.
    
    Args:
        report: Report object
        
    Returns:
        Dictionary suitable for JSON serialization
    """
    return {
        "query": report.query,
        "generated_at": report.generated_at,
        "total_papers_used": report.total_papers_used,
        "introduction": report.introduction,
        "current_research": [
            {
                "title": item.title,
                "summary": item.summary,
                "paper_ids": item.paper_ids,
            }
            for item in report.current_research
        ],
        "open_problems": [
            {
                "title": prob.title,
                "text": prob.text,
                "paper_ids": prob.paper_ids,
            }
            for prob in report.open_problems
        ],
        "conclusion": report.conclusion,
        "paper_cards": [
            {
                "id": card.id,
                "title": card.title,
                "claim": card.claim,
                "paradigm_tags": card.paradigm_tags,
                "data_benchmark": card.data_benchmark,
                "measured": card.measured,
                "limitation": card.limitation,
                "key_quote": card.key_quote,
                "year": card.year,
                "citation_count": card.citation_count,
                "elo_rating": card.elo_rating,
            }
            for card in report.paper_cards
        ],
    }
