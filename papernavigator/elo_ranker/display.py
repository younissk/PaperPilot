"""Rich UI components for Elo ranking display."""


from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.text import Text

from papernavigator.elo_ranker.models import CandidateElo, MatchResult

# Shared console instance
console = Console()


def create_standings_table(
    candidates: list[CandidateElo],
    initial_elo: float = 1500.0,
    top_n: int = 10
) -> Table:
    """Create a Rich table showing current Elo standings."""
    table = Table(
        title="[bold cyan]Live Elo Standings[/bold cyan]",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold magenta",
        title_justify="left",
    )

    table.add_column("Rank", style="dim", width=5, justify="center")
    table.add_column("Elo", style="yellow", width=8, justify="right")
    table.add_column("W/L/D", style="green", width=10, justify="center")
    table.add_column("Title", style="cyan", max_width=50, overflow="ellipsis")
    table.add_column("Year", style="dim", width=6, justify="center")

    # Sort by Elo for display
    sorted_candidates = sorted(candidates, key=lambda x: x.elo, reverse=True)

    for i, ce in enumerate(sorted_candidates[:top_n], 1):
        # Determine rank style based on position
        if i == 1:
            rank_style = "[bold gold1]🥇 1[/bold gold1]"
        elif i == 2:
            rank_style = "[bold silver]🥈 2[/bold silver]"
        elif i == 3:
            rank_style = "[bold orange3]🥉 3[/bold orange3]"
        else:
            rank_style = f"[dim]{i}[/dim]"

        # Format W/L/D record
        record = f"{ce.wins}/{ce.losses}/{ce.draws}"

        # Elo change indicator
        elo_diff = ce.elo - initial_elo
        if elo_diff > 0:
            elo_str = f"[green]{ce.elo:.0f}[/green] [dim](+{elo_diff:.0f})[/dim]"
        elif elo_diff < 0:
            elo_str = f"[red]{ce.elo:.0f}[/red] [dim]({elo_diff:.0f})[/dim]"
        else:
            elo_str = f"{ce.elo:.0f}"

        table.add_row(
            rank_style,
            elo_str,
            record,
            ce.candidate.title[:50],
            str(ce.candidate.year or "-"),
        )

    if len(candidates) > top_n:
        table.add_row(
            "...",
            "",
            "",
            f"[dim]and {len(candidates) - top_n} more papers[/dim]",
            "",
        )

    return table


def create_match_panel(current_match: MatchResult | None) -> Panel:
    """Create a panel showing the current match."""
    if current_match:
        content = Text()
        content.append("⚔️  ", style="bold")
        content.append("MATCH IN PROGRESS\n\n", style="bold yellow")

        content.append("Paper 1: ", style="bold cyan")
        content.append(f"{current_match.paper1_title[:60]}...\n", style="white")

        content.append("    vs\n", style="dim")

        content.append("Paper 2: ", style="bold magenta")
        content.append(f"{current_match.paper2_title[:60]}...\n", style="white")

        return Panel(
            content,
            title="[bold]Current Match[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    else:
        return Panel(
            "[dim]Waiting for next match...[/dim]",
            title="[bold]Current Match[/bold]",
            border_style="dim",
            box=box.ROUNDED,
        )


def create_last_result_panel(match_history: list[MatchResult]) -> Panel:
    """Create a panel showing the last match result."""
    if not match_history:
        return Panel(
            "[dim]No matches completed yet[/dim]",
            title="[bold]Last Result[/bold]",
            border_style="dim",
            box=box.ROUNDED,
        )

    last = match_history[-1]
    content = Text()

    if last.winner == 1:
        content.append("🏆 WINNER: ", style="bold green")
        content.append(f"{last.paper1_title[:50]}...\n", style="green")
        content.append("   vs ", style="dim")
        content.append(f"{last.paper2_title[:50]}...\n", style="dim")
    elif last.winner == 2:
        content.append("   ", style="dim")
        content.append(f"{last.paper1_title[:50]}...\n", style="dim")
        content.append("🏆 WINNER: ", style="bold green")
        content.append(f"{last.paper2_title[:50]}...\n", style="green")
    else:
        content.append("🤝 DRAW\n", style="bold yellow")
        content.append(f"   {last.paper1_title[:50]}...\n", style="dim")
        content.append(f"   {last.paper2_title[:50]}...\n", style="dim")

    if last.reason:
        content.append(f"\n[dim]Reason: {last.reason[:60]}[/dim]")

    return Panel(
        content,
        title="[bold]Last Result[/bold]",
        border_style="green" if last.winner else "yellow",
        box=box.ROUNDED,
    )


def create_display(
    progress: Progress,
    task_id: TaskID,
    match_num: int,
    total_matches: int,
    candidates: list[CandidateElo],
    initial_elo: float,
    current_match: MatchResult | None,
    match_history: list[MatchResult]
) -> Group:
    """Create the full display layout."""
    # Update progress
    progress.update(task_id, completed=match_num)

    # Stats summary
    total_completed = len(match_history)
    wins_p1 = sum(1 for m in match_history if m.winner == 1)
    wins_p2 = sum(1 for m in match_history if m.winner == 2)
    draws = sum(1 for m in match_history if m.winner is None)

    stats_text = Text()
    stats_text.append(f"Matches: {total_completed}/{total_matches} | ", style="dim")
    stats_text.append(f"P1 Wins: {wins_p1} | P2 Wins: {wins_p2} | Draws: {draws}", style="dim")

    return Group(
        progress,
        Text(),
        create_standings_table(candidates, initial_elo, top_n=8),
        Text(),
        create_match_panel(current_match),
        create_last_result_panel(match_history),
        stats_text,
    )


def print_final_standings(candidates: list[CandidateElo], initial_elo: float = 1500.0) -> None:
    """Print the final standings table after the tournament."""
    table = Table(
        title="[bold green]Final Elo Rankings[/bold green]",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold magenta",
    )

    table.add_column("Rank", style="bold", width=6, justify="center")
    table.add_column("Final Elo", style="yellow", width=12, justify="right")
    table.add_column("Change", style="dim", width=10, justify="right")
    table.add_column("W/L/D", style="green", width=10, justify="center")
    table.add_column("Title", style="cyan", max_width=45, overflow="ellipsis")
    table.add_column("Year", style="dim", width=6, justify="center")
    table.add_column("Cites", style="dim", width=7, justify="right")

    for i, ce in enumerate(candidates, 1):
        # Rank medal
        if i == 1:
            rank_str = "🥇 1"
        elif i == 2:
            rank_str = "🥈 2"
        elif i == 3:
            rank_str = "🥉 3"
        else:
            rank_str = str(i)

        # Elo change
        elo_diff = ce.elo - initial_elo
        if elo_diff > 0:
            change_str = f"[green]+{elo_diff:.0f}[/green]"
        elif elo_diff < 0:
            change_str = f"[red]{elo_diff:.0f}[/red]"
        else:
            change_str = "0"

        # Record
        record = f"{ce.wins}/{ce.losses}/{ce.draws}"

        table.add_row(
            rank_str,
            f"{ce.elo:.0f}",
            change_str,
            record,
            ce.candidate.title[:45],
            str(ce.candidate.year or "-"),
            str(ce.candidate.citation_count),
        )

    console.print(table)
