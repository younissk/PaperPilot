"""Event system for decoupling core logic from presentation.

This module defines an event protocol and event dataclasses that allow
core modules to emit events without knowing about Rich or other presentation
layers. Presentation layers (CLI, API) can subscribe to these events
and render them appropriately.
"""

from typing import TYPE_CHECKING, Any, Protocol

from papernavigator.models import AcceptedPaper, SnowballCandidate

if TYPE_CHECKING:
    from papernavigator.elo_ranker.models import CandidateElo, MatchResult


class EventHandler(Protocol):
    """Protocol for event handlers that process events from core modules."""

    def on_progress(
        self,
        current: int,
        total: int,
        message: str,
        **kwargs: Any
    ) -> None:
        """Called when progress updates occur.
        
        Args:
            current: Current progress value
            total: Total expected value
            message: Progress message
            **kwargs: Additional context
        """
        ...

    def on_paper_accepted(
        self,
        paper: AcceptedPaper,
        **kwargs: Any
    ) -> None:
        """Called when a paper is accepted during snowballing.
        
        Args:
            paper: The accepted paper
            **kwargs: Additional context
        """
        ...

    def on_paper_rejected(
        self,
        paper: SnowballCandidate,
        reason: str,
        **kwargs: Any
    ) -> None:
        """Called when a paper is rejected during snowballing.
        
        Args:
            paper: The rejected paper candidate
            reason: Rejection reason
            **kwargs: Additional context
        """
        ...

    def on_match_complete(
        self,
        match: "MatchResult",
        **kwargs: Any
    ) -> None:
        """Called when an Elo match completes.
        
        Args:
            match: The completed match result
            **kwargs: Additional context
        """
        ...

    def on_match_start(
        self,
        paper1_title: str,
        paper2_title: str,
        **kwargs: Any
    ) -> None:
        """Called when an Elo match starts.
        
        Args:
            paper1_title: Title of first paper
            paper2_title: Title of second paper
            **kwargs: Additional context
        """
        ...

    def on_elo_update(
        self,
        candidates: list["CandidateElo"],
        match_num: int,
        total_matches: int,
        **kwargs: Any
    ) -> None:
        """Called when Elo ratings are updated after a match.
        
        Args:
            candidates: Current list of candidates with Elo ratings
            match_num: Current match number
            total_matches: Total expected matches
            **kwargs: Additional context
        """
        ...

    def on_iteration_start(
        self,
        iteration: int,
        frontier_size: int,
        **kwargs: Any
    ) -> None:
        """Called when a snowball iteration starts.
        
        Args:
            iteration: Iteration number
            frontier_size: Number of papers in current frontier
            **kwargs: Additional context
        """
        ...

    def on_iteration_complete(
        self,
        iteration: int,
        accepted: int,
        rejected: int,
        total_accepted: int,
        **kwargs: Any
    ) -> None:
        """Called when a snowball iteration completes.
        
        Args:
            iteration: Iteration number
            accepted: Papers accepted this iteration
            rejected: Papers rejected this iteration
            total_accepted: Total papers accepted so far
            **kwargs: Additional context
        """
        ...

    def on_snowball_stop(
        self,
        reason: str,
        total_accepted: int,
        total_visited: int,
        **kwargs: Any
    ) -> None:
        """Called when snowballing stops.
        
        Args:
            reason: Reason for stopping
            total_accepted: Total papers accepted
            total_visited: Total papers visited
            **kwargs: Additional context
        """
        ...


class NullEventHandler:
    """Null event handler that does nothing.
    
    Useful as a default when no event handling is needed.
    """

    def on_progress(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_paper_accepted(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_paper_rejected(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_match_complete(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_match_start(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_elo_update(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_iteration_start(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_iteration_complete(self, *args: Any, **kwargs: Any) -> None:
        pass

    def on_snowball_stop(self, *args: Any, **kwargs: Any) -> None:
        pass
