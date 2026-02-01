"""Report generation module for PaperPilot.

This module provides citation-safe research report generation using a
multi-step LLM pipeline with paper cards, outline planning, section
writing with enforced citations, and citation auditing.

Main entry point:
    from papernavigator.report import generate_report

Example:
    from pathlib import Path
    from papernavigator.report import generate_report, report_to_dict
    
    report = await generate_report(
        snowball_file=Path("results/my_query/snowball.json"),
        elo_file=Path("results/my_query/elo_ranked.json"),
        top_k=30,
    )
    
    report_data = report_to_dict(report)
"""

from papernavigator.report.auditor import (
    audit_all_sections,
    audit_section,
)
from papernavigator.report.cards import (
    generate_paper_card,
    generate_paper_cards,
)
from papernavigator.report.generator import (
    generate_report,
    load_papers_from_file,
    report_to_dict,
    select_top_k_papers,
)
from papernavigator.report.models import (
    AuditResult,
    OpenProblem,
    PaperCard,
    Report,
    ReportOutline,
    ResearchItem,
    SectionPlan,
    SentenceAudit,
    WrittenSection,
)
from papernavigator.report.outline import (
    generate_outline,
    group_by_tags,
)
from papernavigator.report.writer import (
    extract_cited_ids,
    write_all_sections,
    write_conclusion,
    write_introduction,
    write_section,
)

__all__ = [
    # Models
    "PaperCard",
    "SectionPlan",
    "ReportOutline",
    "SentenceAudit",
    "AuditResult",
    "WrittenSection",
    "ResearchItem",
    "OpenProblem",
    "Report",
    # Generator
    "generate_report",
    "report_to_dict",
    "select_top_k_papers",
    "load_papers_from_file",
    # Cards
    "generate_paper_cards",
    "generate_paper_card",
    # Outline
    "generate_outline",
    "group_by_tags",
    # Writer
    "write_section",
    "write_all_sections",
    "write_introduction",
    "write_conclusion",
    "extract_cited_ids",
    # Auditor
    "audit_section",
    "audit_all_sections",
]
