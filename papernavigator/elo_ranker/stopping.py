"""Early stopping strategies for Elo ranking."""


from papernavigator.elo_ranker.models import CandidateElo


class StabilityChecker:
    """Checks if the top-K rankings have stabilized."""

    def __init__(
        self,
        top_k: int = 30,
        check_interval: int = 50,
        threshold: float = 0.9
    ):
        """Initialize stability checker.
        
        Args:
            top_k: Number of top candidates to track
            check_interval: Check stability every N matches
            threshold: Overlap threshold (0-1) to consider stable
        """
        self.top_k = top_k
        self.check_interval = check_interval
        self.threshold = threshold
        self.snapshots: list[list[str]] = []
        self.match_count = 0

    def check(self, candidates: list[CandidateElo]) -> bool:
        """Check if rankings have stabilized.
        
        Args:
            candidates: Current list of candidates with Elo ratings
            
        Returns:
            True if stable (should stop), False otherwise
        """
        self.match_count += 1

        # Only check at intervals
        if self.match_count % self.check_interval != 0:
            return False

        # Get top-K paper IDs
        sorted_candidates = sorted(candidates, key=lambda x: x.elo, reverse=True)
        top_ids = [c.candidate.paper_id for c in sorted_candidates[:self.top_k]]

        # Need at least 2 snapshots to compare
        if len(self.snapshots) >= 2:
            # Compare with last snapshot
            last_snapshot = self.snapshots[-1]
            overlap = len(set(top_ids) & set(last_snapshot)) / self.top_k

            if overlap >= self.threshold:
                return True  # Stable, stop early

        # Store current snapshot
        self.snapshots.append(top_ids)

        # Keep only last 3 snapshots to avoid memory growth
        if len(self.snapshots) > 3:
            self.snapshots.pop(0)

        return False


class TournamentRounds:
    """Manages tournament-style rounds with progressive filtering."""

    def __init__(self, rounds: list[tuple[int, int]]):
        """Initialize tournament rounds.
        
        Args:
            rounds: List of (top_n, matches) tuples
                   e.g., [(0, 50), (80, 100), (40, 100)]
                   means: all papers get 50 matches, then top 80 get 100, then top 40 get 100
        """
        self.rounds = rounds
        self.current_round = 0
        self.matches_in_round = 0
        self.active_candidates: list[CandidateElo] = []

    def get_active_candidates(self, all_candidates: list[CandidateElo]) -> list[CandidateElo]:
        """Get candidates active in current round.
        
        Args:
            all_candidates: All candidates with Elo ratings
            
        Returns:
            List of candidates active in current round
        """
        if self.current_round >= len(self.rounds):
            return []  # Tournament complete

        top_n, _ = self.rounds[self.current_round]

        if top_n == 0:
            # Round 0 means all candidates
            return all_candidates

        # Sort and take top N
        sorted_candidates = sorted(all_candidates, key=lambda x: x.elo, reverse=True)
        return sorted_candidates[:top_n]

    def should_advance_round(self) -> bool:
        """Check if we should advance to next round.
        
        Returns:
            True if should advance, False otherwise
        """
        if self.current_round >= len(self.rounds):
            return False

        _, max_matches = self.rounds[self.current_round]
        return self.matches_in_round >= max_matches

    def advance_round(self) -> bool:
        """Advance to next round.
        
        Returns:
            True if tournament continues, False if complete
        """
        self.current_round += 1
        self.matches_in_round = 0
        return self.current_round < len(self.rounds)

    def record_match(self) -> None:
        """Record that a match was played in current round."""
        self.matches_in_round += 1

    def is_complete(self) -> bool:
        """Check if tournament is complete.
        
        Returns:
            True if all rounds are done
        """
        return self.current_round >= len(self.rounds)
