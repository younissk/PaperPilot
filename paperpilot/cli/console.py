"""Rich console utilities for beautiful CLI output.

This module provides a centralized console instance and reusable
display components for tables, panels, progress bars, and status spinners.
"""

from typing import TYPE_CHECKING, Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from paperpilot.core.models import AcceptedPaper, QueryProfile

# Shared console instance
console = Console()


def print_header(text: str, style: str = "bold blue") -> None:
    """Print a styled header rule."""
    console.print()
    console.print(Rule(f"[{style}]{text}[/{style}]", style=style))
    console.print()


def print_step(step: int, description: str) -> None:
    """Print a step indicator."""
    console.print(f"[bold cyan]Step {step}:[/bold cyan] {description}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]ℹ[/dim] {message}")


def display_query_profile(profile: "QueryProfile") -> None:
    """Display a query profile in a beautiful panel with tables."""
    # Create the main content
    content = Text()

    # Domain description
    content.append("Domain: ", style="bold")
    content.append(f"{profile.domain_description}\n\n", style="cyan")

    # Required concept groups
    content.append("Required Concept Groups ", style="bold")
    content.append("(OR within, AND across):\n", style="dim")

    for i, group in enumerate(profile.required_concept_groups, 1):
        content.append(f"  {i}. ", style="bold green")
        content.append(" | ".join(group), style="green")
        content.append("\n")

    content.append("\n")

    # Boundaries
    content.append("Boundaries: ", style="bold")
    content.append(profile.domain_boundaries, style="yellow")

    panel = Panel(
        content,
        title="[bold]Query Profile[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)


def display_augmented_queries(queries: list[str], time_taken: float) -> None:
    """Display augmented queries in a panel."""
    content = Text()
    for i, query in enumerate(queries, 1):
        content.append(f"{i}. ", style="bold cyan")
        content.append(f"{query}\n", style="white")

    panel = Panel(
        content,
        title=f"[bold]Augmented Queries[/bold] [dim](generated in {time_taken:.2f}s)[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(panel)


def display_papers_table(
    papers: list[Any],
    title: str,
    show_link: bool = False,
    show_depth: bool = False,
    show_judge: bool = False,
    max_rows: int | None = None,
) -> None:
    """Display papers in a formatted table.
    
    Args:
        papers: List of paper objects (ReducedArxivEntry, AcceptedPaper, etc.)
        title: Table title
        show_link: Whether to show links column
        show_depth: Whether to show depth column
        show_judge: Whether to show judge reason
        max_rows: Maximum rows to display (None for all)
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold magenta",
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", max_width=55, overflow="ellipsis")
    table.add_column("Year", style="green", justify="center", width=6)
    table.add_column("Citations", style="yellow", justify="right", width=10)

    if show_depth:
        table.add_column("Depth", style="blue", justify="center", width=6)
    if show_link:
        table.add_column("Link", style="dim", max_width=30, overflow="ellipsis")
    if show_judge:
        table.add_column("Reason", style="dim", max_width=30, overflow="ellipsis")

    display_papers = papers[:max_rows] if max_rows else papers

    for i, paper in enumerate(display_papers, 1):
        row = [
            str(i),
            getattr(paper, 'title', str(paper))[:55],
            str(getattr(paper, 'year', '-') or '-'),
            str(getattr(paper, 'citation_count', 0)),
        ]

        if show_depth:
            row.append(str(getattr(paper, 'depth', '-')))
        if show_link:
            row.append(getattr(paper, 'link', '-') or '-')
        if show_judge:
            reason = getattr(paper, 'judge_reason', '-') or '-'
            row.append(reason[:30] if len(reason) > 30 else reason)

        table.add_row(*row)

    if max_rows and len(papers) > max_rows:
        table.add_row("...", f"[dim]and {len(papers) - max_rows} more[/dim]", "", "")

    console.print(table)


def display_filtering_results(
    filtered: list[Any],
    discarded: list[Any],
    time_taken: float
) -> None:
    """Display filtering results summary."""
    panel_content = Text()
    panel_content.append("Relevant: ", style="bold")
    panel_content.append(f"{len(filtered)}", style="bold green")
    panel_content.append(" | ")
    panel_content.append("Discarded: ", style="bold")
    panel_content.append(f"{len(discarded)}", style="bold red")
    panel_content.append(f"\n[dim]Completed in {time_taken:.2f}s[/dim]")

    panel = Panel(
        panel_content,
        title="[bold]Filtering Results[/bold]",
        border_style="green" if filtered else "yellow",
        box=box.ROUNDED,
    )
    console.print(panel)


def display_snowball_config(
    max_iterations: int,
    top_n: int,
    min_threshold: int,
    max_accepted: int,
    max_refs: int,
    max_citations: int,
) -> None:
    """Display snowball engine configuration."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Max iterations", str(max_iterations))
    table.add_row("Top N per iteration", str(top_n))
    table.add_row("Min new papers threshold", str(min_threshold))
    table.add_row("Max total accepted", str(max_accepted))
    table.add_row("Max refs/citations per paper", f"{max_refs}/{max_citations}")

    panel = Panel(
        table,
        title="[bold]Snowball Engine Configuration[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)


def display_iteration_header(iteration: int, frontier_size: int) -> None:
    """Display a header for snowball iteration."""
    console.print()
    console.print(Rule(
        f"[bold yellow]Iteration {iteration}[/bold yellow] — Expanding from {frontier_size} papers",
        style="yellow"
    ))


def display_seed_paper(title: str, paper_id: str, idx: int) -> None:
    """Display a seed paper entry."""
    console.print(f"  [bold green]{idx}.[/bold green] {title[:70]}...")
    console.print(f"     [dim]ID: {paper_id}[/dim]")


def display_accept_reject(
    title: str,
    accepted: bool,
    reason: str,
) -> None:
    """Display accept/reject decision for a paper."""
    if accepted:
        console.print(f"  [bold green]✓ ACCEPT[/bold green] {title[:60]}...")
        console.print(f"    [dim]{reason}[/dim]")
    else:
        console.print(f"  [bold red]✗ REJECT[/bold red] {title[:60]}...")
        console.print(f"    [dim]{reason}[/dim]")


def display_snowball_summary(
    accepted: list["AcceptedPaper"],
    visited_count: int,
    paper_titles: dict,
) -> None:
    """Display final snowball summary with statistics."""
    from paperpilot.core.models import EdgeType

    # Calculate breakdowns
    seeds = [p for p in accepted if p.edge_type == EdgeType.SEED]
    refs = [p for p in accepted if p.edge_type == EdgeType.REFERENCE]
    cites = [p for p in accepted if p.edge_type == EdgeType.CITATION]

    depths = {}
    for p in accepted:
        depths[p.depth] = depths.get(p.depth, 0) + 1

    # Statistics panel
    stats = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    stats.add_column("Metric", style="bold")
    stats.add_column("Value", style="cyan", justify="right")

    stats.add_row("Total Accepted", f"[bold green]{len(accepted)}[/bold green]")
    stats.add_row("Total Visited", str(visited_count))
    stats.add_row("", "")
    stats.add_row("[bold]By Discovery Method[/bold]", "")
    stats.add_row("  Seeds", str(len(seeds)))
    stats.add_row("  References (backward)", str(len(refs)))
    stats.add_row("  Citations (forward)", str(len(cites)))
    stats.add_row("", "")
    stats.add_row("[bold]By Depth[/bold]", "")
    for d in sorted(depths.keys()):
        stats.add_row(f"  Depth {d}", str(depths[d]))

    stats_panel = Panel(
        stats,
        title="[bold]Summary Statistics[/bold]",
        border_style="green",
        box=box.ROUNDED,
    )

    # Top papers table
    top_table = Table(
        title="Top 10 by Citations",
        box=box.SIMPLE,
        show_lines=False,
        header_style="bold",
    )
    top_table.add_column("#", style="dim", width=3)
    top_table.add_column("Citations", style="yellow", justify="right", width=8)
    top_table.add_column("Title", style="cyan", max_width=50, overflow="ellipsis")
    top_table.add_column("Year", style="green", width=6)

    sorted_by_cites = sorted(accepted, key=lambda p: p.citation_count, reverse=True)
    for i, p in enumerate(sorted_by_cites[:10], 1):
        top_table.add_row(
            str(i),
            str(p.citation_count),
            p.title[:50],
            str(p.year or "-"),
        )

    console.print()
    print_header("Snowball Engine — Final Summary", "bold green")
    console.print(stats_panel)
    console.print()
    console.print(top_table)


def display_export_success(output_file: str, count: int, query: str) -> None:
    """Display export success message."""
    content = Text()
    content.append("File: ", style="bold")
    content.append(f"{output_file}\n", style="cyan")
    content.append("Papers: ", style="bold")
    content.append(f"{count}\n", style="green")
    content.append("Query: ", style="bold")
    content.append(query, style="yellow")

    panel = Panel(
        content,
        title="[bold green]Results Exported[/bold green]",
        border_style="green",
        box=box.ROUNDED,
    )
    console.print(panel)


def create_progress() -> Progress:
    """Create a pre-configured progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def create_spinner_progress() -> Progress:
    """Create a simple spinner progress for indeterminate tasks."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    )


def display_resolve_result(
    title: str,
    success: bool,
    openalex_id: str | None = None,
    citations: int | None = None,
    year: int | None = None,
) -> None:
    """Display OpenAlex resolution result."""
    if success:
        year_str = f"({year})" if year else ""
        console.print(f"  [green]✓[/green] {title[:55]}...")
        console.print(f"    [dim]ID: {openalex_id} | Citations: {citations} {year_str}[/dim]")
    else:
        console.print(f"  [red]✗[/red] {title[:55]}...")
        console.print("    [dim]Could not resolve to OpenAlex ID[/dim]")


def display_expand_result(
    title: str,
    refs_found: int,
    refs_new: int,
    cites_found: int,
    cites_new: int,
) -> None:
    """Display expansion results for a paper."""
    console.print(f"  [cyan]→[/cyan] {title[:50]}...")
    console.print(
        f"    [dim]Refs: {refs_found} found, {refs_new} new | "
        f"Citations: {cites_found} found, {cites_new} new[/dim]"
    )


def display_ranking_summary(
    ranked_count: int,
    passed_gate: int,
    total: int,
    top_papers: list[Any],
) -> None:
    """Display ranking summary."""
    console.print("[bold]Ranking Summary:[/bold]")
    console.print(f"  Total candidates: {total}")
    console.print(f"  Passed keyword gate: [green]{passed_gate}[/green]")
    console.print(f"  Top ranked for judging: [cyan]{ranked_count}[/cyan]")

    if top_papers:
        console.print("\n[bold]Top 5 candidates:[/bold]")
        for i, p in enumerate(top_papers[:5], 1):
            score = getattr(p, 'priority_score', 0)
            console.print(f"  {i}. [dim]{score:.2f}[/dim] {p.title[:55]}...")


def display_iteration_result(accepted: int, rejected: int) -> None:
    """Display iteration results."""
    console.print()
    console.print(
        f"[bold]Iteration Result:[/bold] "
        f"[green]Accepted: {accepted}[/green] | "
        f"[red]Rejected: {rejected}[/red]"
    )


def display_status(
    total_accepted: int,
    total_visited: int,
    new_this_iteration: int,
) -> None:
    """Display current status."""
    console.print(
        f"[dim]Status: {total_accepted} accepted, "
        f"{total_visited} visited, "
        f"{new_this_iteration} new this iteration[/dim]"
    )


def display_stop_reason(reason: str) -> None:
    """Display stop reason."""
    console.print()
    console.print(f"[bold yellow]STOP:[/bold yellow] {reason}")


def display_clusters_table(
    cluster_summaries: list[Any],
    total_papers: int,
    method: str,
    dim_reduction: str,
) -> None:
    """Display cluster analysis results in Rich format.
    
    Shows a header panel with summary, followed by a tree-style display
    of each cluster with its top papers.
    
    Args:
        cluster_summaries: List of ClusterSummary objects
        total_papers: Total number of papers clustered
        method: Clustering method used ("hdbscan" or "kmeans")
        dim_reduction: Dimension reduction method ("umap" or "tsne")
    """
    from rich.tree import Tree

    # Header panel
    n_clusters = len([c for c in cluster_summaries if c.cluster_id != -1])
    header_text = Text()
    header_text.append("Cluster Analysis: ", style="bold")
    header_text.append(f"{total_papers} papers", style="cyan")
    header_text.append(" → ", style="dim")
    header_text.append(f"{n_clusters} clusters", style="green")
    header_text.append("\n")
    header_text.append(f"Method: {method.upper()} + {dim_reduction.upper()}", style="dim")

    header_panel = Panel(
        header_text,
        border_style="blue",
        box=box.DOUBLE,
    )
    console.print(header_panel)
    console.print()

    # Sort clusters by count descending, but put noise (-1) last
    sorted_summaries = sorted(
        cluster_summaries,
        key=lambda c: (c.cluster_id == -1, -c.count),
    )

    # Display each cluster as a tree
    for summary in sorted_summaries:
        if summary.cluster_id == -1:
            cluster_style = "dim"
            marker = "○"
        else:
            cluster_style = "bold cyan"
            marker = "●"

        # Create tree for this cluster
        tree = Tree(
            f"[{cluster_style}]{marker} {summary.label}[/{cluster_style}] "
            f"[dim]({summary.count} papers)[/dim]"
        )

        # Add top papers as branches
        for i, paper in enumerate(summary.top_papers[:3]):
            title = paper.get("title", "Unknown")
            if len(title) > 60:
                title = title[:57] + "..."
            year = paper.get("year", "?")
            citations = paper.get("citations", 0)

            paper_text = f"[cyan]{title}[/cyan] [dim]({year}, {citations} cites)[/dim]"
            tree.add(paper_text)

        if summary.count > 3:
            tree.add(f"[dim]... and {summary.count - 3} more[/dim]")

        console.print(tree)
        console.print()


def display_cluster_export_success(
    json_path: str,
    html_path: str,
    n_papers: int,
    n_clusters: int,
) -> None:
    """Display cluster export success message.
    
    Args:
        json_path: Path to exported JSON file
        html_path: Path to exported HTML visualization
        n_papers: Number of papers clustered
        n_clusters: Number of clusters found
    """
    content = Text()
    content.append("JSON: ", style="bold")
    content.append(f"{json_path}\n", style="cyan")
    content.append("HTML: ", style="bold")
    content.append(f"{html_path}\n", style="cyan")
    content.append("Papers: ", style="bold")
    content.append(f"{n_papers}\n", style="green")
    content.append("Clusters: ", style="bold")
    content.append(str(n_clusters), style="yellow")

    panel = Panel(
        content,
        title="[bold green]Clustering Complete[/bold green]",
        border_style="green",
        box=box.ROUNDED,
    )
    console.print(panel)
