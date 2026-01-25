"""Report generation module for PaperPilot.

This module provides citation-safe research report generation using a
multi-step LLM pipeline with paper cards, outline planning, section
writing with enforced citations, and citation auditing.

Main entry point:
    from paperpilot.core.report import generate_report

Example:
    from pathlib import Path
    from paperpilot.core.report import generate_report, report_to_dict
    
    report = await generate_report(
        snowball_file=Path("results/my_query/snowball.json"),
        elo_file=Path("results/my_query/elo_ranked.json"),
        top_k=30,
    )
    
    report_data = report_to_dict(report)
"""

from paperpilot.core.report.models import (
    PaperCard,
    SectionPlan,
    ReportOutline,
    SentenceAudit,
    AuditResult,
    WrittenSection,
    ResearchItem,
    OpenProblem,
    Report,
)

from paperpilot.core.report.generator import (
    generate_report,
    report_to_dict,
    select_top_k_papers,
    load_papers_from_file,
)

from paperpilot.core.report.cards import (
    generate_paper_cards,
    generate_paper_card,
)

from paperpilot.core.report.outline import (
    generate_outline,
    group_by_tags,
)

from paperpilot.core.report.writer import (
    write_section,
    write_all_sections,
    write_introduction,
    write_conclusion,
    extract_cited_ids,
)

from paperpilot.core.report.auditor import (
    audit_section,
    audit_all_sections,
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
