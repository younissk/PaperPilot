"""Rich event handlers for CLI presentation.

This module provides RichEventHandler that implements the EventHandler
protocol and renders events using Rich console components.
"""

from typing import Any

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn

from paperpilot.cli.console import (
    display_accept_reject,
    display_iteration_header,
    display_iteration_result,
    display_snowball_summary,
    display_status,
    display_stop_reason,
)
from paperpilot.core.elo_ranker.display import (
    create_display as create_elo_display,
)
from paperpilot.core.elo_ranker.display import (
    print_final_standings,
)
from paperpilot.core.elo_ranker.models import (  # Import here to avoid circular import
    CandidateElo,
    MatchResult,
)
from paperpilot.core.events import EventHandler
from paperpilot.core.models import AcceptedPaper, SnowballCandidate


class RichEventHandler(EventHandler):
    """Rich-based event handler for CLI presentation."""

    def __init__(self, console: Console | None = None):
        """Initialize the Rich event handler.
        
        Args:
            console: Rich Console instance (uses default if None)
        """
        self.console = console or Console()
        self._elo_progress: Progress | None = None
        self._elo_task_id: TaskID | None = None
        self._elo_live: Live | None = None
        self._elo_match_history: list[MatchResult] = []
        self._elo_current_match: MatchResult | None = None
        self._elo_initial_elo: float = 1500.0
        self._elo_max_matches: int = 0

    def on_progress(
        self,
        current: int,
        total: int,
        message: str,
        **kwargs: Any
    ) -> None:
        """Display progress updates."""
        if self._elo_progress and self._elo_task_id is not None:
            self._elo_progress.update(self._elo_task_id, completed=current, description=message)
        else:
            # Simple progress display
            self.console.print(f"[dim]{message}: {current}/{total}[/dim]")

    def on_paper_accepted(
        self,
        paper: AcceptedPaper,
        **kwargs: Any
    ) -> None:
        """Display accepted paper."""
        display_accept_reject(
            paper.title,
            accepted=True,
            reason=paper.judge_reason or "Accepted",
        )

    def on_paper_rejected(
        self,
        paper: SnowballCandidate,
        reason: str,
        **kwargs: Any
    ) -> None:
        """Display rejected paper."""
        display_accept_reject(
            paper.title,
            accepted=False,
            reason=reason,
        )

    def on_match_complete(
        self,
        match: MatchResult,
        **kwargs: Any
    ) -> None:
        """Handle match completion."""
        self._elo_match_history.append(match)
        self._elo_current_match = None

        # Update display if live
        if self._elo_live and self._elo_progress and self._elo_task_id is not None:
            match_num = len(self._elo_match_history)
            candidates = kwargs.get("candidates", [])
            self._elo_live.update(
                create_elo_display(
                    self._elo_progress,
                    self._elo_task_id,
                    match_num,
                    self._elo_max_matches,
                    candidates,
                    self._elo_initial_elo,
                    self._elo_current_match,
                    self._elo_match_history,
                )
            )

    def on_match_start(
        self,
        paper1_title: str,
        paper2_title: str,
        **kwargs: Any
    ) -> None:
        """Handle match start."""
        self._elo_current_match = MatchResult(
            paper1_title=paper1_title,
            paper2_title=paper2_title,
            winner=None,
            reason="",
        )

        # Update display if live
        if self._elo_live and self._elo_progress and self._elo_task_id is not None:
            match_num = len(self._elo_match_history)
            candidates = kwargs.get("candidates", [])
            self._elo_live.update(
                create_elo_display(
                    self._elo_progress,
                    self._elo_task_id,
                    match_num,
                    self._elo_max_matches,
                    candidates,
                    self._elo_initial_elo,
                    self._elo_current_match,
                    self._elo_match_history,
                )
            )

    def on_elo_update(
        self,
        candidates: list[CandidateElo],
        match_num: int,
        total_matches: int,
        **kwargs: Any
    ) -> None:
        """Handle Elo rating updates."""
        # Update display if live
        if self._elo_live and self._elo_progress and self._elo_task_id is not None:
            self._elo_live.update(
                create_elo_display(
                    self._elo_progress,
                    self._elo_task_id,
                    match_num,
                    total_matches,
                    candidates,
                    self._elo_initial_elo,
                    self._elo_current_match,
                    self._elo_match_history,
                )
            )

    def on_iteration_start(
        self,
        iteration: int,
        frontier_size: int,
        **kwargs: Any
    ) -> None:
        """Display iteration start."""
        display_iteration_header(iteration, frontier_size)

    def on_iteration_complete(
        self,
        iteration: int,
        accepted: int,
        rejected: int,
        total_accepted: int,
        **kwargs: Any
    ) -> None:
        """Display iteration completion."""
        display_iteration_result(accepted, rejected)
        display_status(
            total_accepted=total_accepted,
            total_visited=kwargs.get("total_visited", 0),
            new_this_iteration=accepted,
        )

    def on_snowball_stop(
        self,
        reason: str,
        total_accepted: int,
        total_visited: int,
        **kwargs: Any
    ) -> None:
        """Display snowball stop."""
        display_stop_reason(reason)
        accepted_papers = kwargs.get("accepted_papers", [])
        paper_titles = kwargs.get("paper_titles", {})
        if accepted_papers:
            display_snowball_summary(accepted_papers, total_visited, paper_titles)

    def start_elo_display(
        self,
        candidates: list[CandidateElo],
        max_matches: int,
        initial_elo: float = 1500.0,
        config_info: dict | None = None,
    ) -> None:
        """Start the Elo ranking live display.
        
        Args:
            candidates: Initial list of candidates
            max_matches: Maximum number of matches
            initial_elo: Initial Elo rating
            config_info: Optional configuration info to display
        """

        self._elo_initial_elo = initial_elo
        self._elo_max_matches = max_matches
        self._elo_match_history = []
        self._elo_current_match = None

        # Create progress bar
        self._elo_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total} matches)"),
            console=self.console,
        )
        self._elo_task_id = self._elo_progress.add_task(
            "[cyan]Running Elo matches...",
            total=max_matches
        )

        # Print header
        if config_info:
            self.console.print()
            self.console.print(Panel(
                f"[bold]Elo Ranking Tournament[/bold]\n\n"
                f"Papers: {config_info.get('papers', len(candidates))} | "
                f"Max Matches: {max_matches} | "
                f"K-factor: {config_info.get('k_factor', 32.0)} | "
                f"Pairing: {config_info.get('pairing', 'swiss')} | "
                f"Concurrency: {config_info.get('concurrency', 5)}",
                title="[bold cyan]🏆 Paper Battle Arena 🏆[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE,
            ))
            self.console.print()

        # Start live display
        self._elo_live = Live(
            create_elo_display(
                self._elo_progress,
                self._elo_task_id,
                0,
                max_matches,
                candidates,
                initial_elo,
                None,
                [],
            ),
            console=self.console,
            refresh_per_second=4,
            transient=False,
        )
        self._elo_live.__enter__()

    def stop_elo_display(self, candidates: list[CandidateElo], final: bool = True) -> None:
        """Stop the Elo ranking live display.
        
        Args:
            candidates: Final list of candidates
            final: If True, print final standings
        """
        if self._elo_live:
            self._elo_live.__exit__(None, None, None)
            self._elo_live = None

        if final:
            self.console.print()
            self.console.print(Panel(
                "[bold green]Tournament Complete![/bold green]",
                border_style="green",
                box=box.DOUBLE,
            ))
            self.console.print()
            print_final_standings(candidates, self._elo_initial_elo)

        self._elo_progress = None
        self._elo_task_id = None
        self._elo_match_history = []
        self._elo_current_match = None
