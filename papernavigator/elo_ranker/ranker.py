"""Main EloRanker orchestrator integrating all components."""


from papernavigator.elo_ranker.elo import update_elo
from papernavigator.elo_ranker.judge import judge_match_batch
from papernavigator.elo_ranker.models import CandidateElo, MatchResult, RankerConfig
from papernavigator.elo_ranker.pairing import PairingStrategy, RandomPairing, SwissPairing
from papernavigator.elo_ranker.stopping import StabilityChecker, TournamentRounds
from papernavigator.events import EventHandler, NullEventHandler
from papernavigator.models import QueryProfile, SnowballCandidate


class EloRanker:
    """Elo ranking system for academic papers using pairwise LLM comparisons.
    
    Uses the standard Elo rating system where papers "battle" each other
    and ratings are updated based on match outcomes. The LLM judges which
    paper is more relevant to the query profile.
    
    Features:
    - Swiss-style pairing for informative matches
    - Relevance-first prompts (quality as tiebreaker only)
    - Early stopping when rankings stabilize
    - Concurrent match execution for speed
    - Rich interactive display
    """

    def __init__(
        self,
        profile: QueryProfile,
        candidates: list[SnowballCandidate],
        config: RankerConfig | None = None,
        event_handler: EventHandler | None = None
    ):
        """Initialize the Elo ranker.
        
        Args:
            profile: Query profile for relevance judgment
            candidates: List of paper candidates to rank
            config: Configuration for ranking behavior (uses defaults if None)
            event_handler: Optional event handler for progress updates (uses NullHandler if None)
        """
        self.profile = profile
        self.config = config or RankerConfig()
        self.event_handler = event_handler or NullEventHandler()

        # Initialize candidates with Elo ratings
        self.elo_candidates = [
            CandidateElo(candidate=candidate, elo=self.config.initial_elo)
            for candidate in candidates
        ]

        # Match history for display
        self.match_history: list[MatchResult] = []
        self.current_match: MatchResult | None = None

        # Pairing strategy
        if self.config.pairing_strategy == "swiss":
            self.pairing: PairingStrategy = SwissPairing()
        else:
            self.pairing: PairingStrategy = RandomPairing()

        # Early stopping
        self.stability_checker: StabilityChecker | None = None
        if self.config.early_stop_enabled and not self.config.tournament_mode:
            self.stability_checker = StabilityChecker(
                top_k=self.config.early_stop_top_k,
                check_interval=self.config.early_stop_check_interval,
                threshold=self.config.early_stop_threshold
            )

        # Tournament rounds
        self.tournament: TournamentRounds | None = None
        if self.config.tournament_mode:
            self.tournament = TournamentRounds(self.config.tournament_rounds)

        # Determine max matches
        if self.config.max_matches is None:
            self.max_matches = len(candidates) * 3
        else:
            self.max_matches = self.config.max_matches

    async def rank_candidates(self) -> list[CandidateElo]:
        """Rank candidates using Elo ranking through pairwise matches.
        
        Runs multiple pairwise matches, updates Elo ratings after each match,
        and returns candidates sorted by final Elo rating.
        
        If interactive mode is enabled, shows a live Rich display with real-time
        standings and match updates.
        
        Returns:
            List of CandidateElo objects sorted by Elo rating (highest first)
        """
        if len(self.elo_candidates) < 2:
            # Need at least 2 candidates to run matches
            return self.elo_candidates

        if self.config.interactive:
            return await self._rank_with_display()
        else:
            return await self._rank_silent()

    async def _rank_silent(self) -> list[CandidateElo]:
        """Run ranking without any display."""
        matches_played = 0
        calibration_matches = self.config.calibration_matches

        while matches_played < self.max_matches:
            # Determine active candidates (for tournament mode)
            if self.tournament:
                active_candidates = self.tournament.get_active_candidates(self.elo_candidates)
                if not active_candidates:
                    break  # Tournament complete
            else:
                active_candidates = self.elo_candidates

            # Select pairing strategy based on calibration phase
            if matches_played < calibration_matches:
                pairing_strategy = RandomPairing()
            else:
                pairing_strategy = self.pairing

            # Select pairs
            batch_size = min(self.config.batch_size, self.max_matches - matches_played)
            pairs = pairing_strategy.select_pairs(active_candidates, batch_size)

            if not pairs:
                break

            # Prepare pairs for judging
            judge_pairs = [
                (p[0].candidate, p[1].candidate) for p in pairs
            ]

            # Emit match start events
            for pair in pairs:
                self.event_handler.on_match_start(
                    paper1_title=pair[0].candidate.title,
                    paper2_title=pair[1].candidate.title,
                    candidates=self.elo_candidates,
                )

            # Judge matches concurrently
            results = await judge_match_batch(
                judge_pairs,
                self.profile,
                concurrency=self.config.concurrency
            )

            # Update Elo ratings and emit events
            for (c1, c2), result in zip(pairs, results):
                update_elo(c1, c2, result.winner, self.config.k_factor)
                self.match_history.append(result)
                matches_played += 1

                # Emit match complete event
                self.event_handler.on_match_complete(
                    match=result,
                    candidates=self.elo_candidates,
                )

                # Emit Elo update event
                self.event_handler.on_elo_update(
                    candidates=self.elo_candidates,
                    match_num=matches_played,
                    total_matches=self.max_matches,
                )

                # Emit progress event
                self.event_handler.on_progress(
                    current=matches_played,
                    total=self.max_matches,
                    message="Running Elo matches...",
                )

                if self.tournament:
                    self.tournament.record_match()
                    if self.tournament.should_advance_round():
                        if not self.tournament.advance_round():
                            break  # Tournament complete

            # Check early stopping
            if self.stability_checker:
                if self.stability_checker.check(self.elo_candidates):
                    break

        # Sort candidates by Elo rating (highest first)
        self.elo_candidates.sort(key=lambda x: x.elo, reverse=True)
        return self.elo_candidates

    async def _rank_with_display(self) -> list[CandidateElo]:
        """Run ranking with interactive display via event handler."""
        # Start display if handler supports it
        if hasattr(self.event_handler, 'start_elo_display'):
            self.event_handler.start_elo_display(
                candidates=self.elo_candidates,
                max_matches=self.max_matches,
                initial_elo=self.config.initial_elo,
                config_info={
                    "papers": len(self.elo_candidates),
                    "k_factor": self.config.k_factor,
                    "pairing": self.config.pairing_strategy,
                    "concurrency": self.config.concurrency,
                },
            )

        matches_played = 0
        calibration_matches = self.config.calibration_matches

        try:
            while matches_played < self.max_matches:
                # Determine active candidates (for tournament mode)
                if self.tournament:
                    active_candidates = self.tournament.get_active_candidates(self.elo_candidates)
                    if not active_candidates:
                        break  # Tournament complete
                else:
                    active_candidates = self.elo_candidates

                # Select pairing strategy based on calibration phase
                if matches_played < calibration_matches:
                    pairing_strategy = RandomPairing()
                else:
                    pairing_strategy = self.pairing

                # Select pairs
                batch_size = min(self.config.batch_size, self.max_matches - matches_played)
                pairs = pairing_strategy.select_pairs(active_candidates, batch_size)

                if not pairs:
                    break

                # Prepare pairs for judging
                judge_pairs = [
                    (p[0].candidate, p[1].candidate) for p in pairs
                ]

                # Emit match start events
                for pair in pairs:
                    self.event_handler.on_match_start(
                        paper1_title=pair[0].candidate.title,
                        paper2_title=pair[1].candidate.title,
                        candidates=self.elo_candidates,
                    )

                # Judge matches concurrently
                results = await judge_match_batch(
                    judge_pairs,
                    self.profile,
                    concurrency=self.config.concurrency
                )

                # Update Elo ratings and emit events
                for (c1, c2), result in zip(pairs, results):
                    update_elo(c1, c2, result.winner, self.config.k_factor)
                    self.match_history.append(result)
                    matches_played += 1

                    # Emit match complete event
                    self.event_handler.on_match_complete(
                        match=result,
                        candidates=self.elo_candidates,
                    )

                    # Emit Elo update event
                    self.event_handler.on_elo_update(
                        candidates=self.elo_candidates,
                        match_num=matches_played,
                        total_matches=self.max_matches,
                    )

                    # Emit progress event
                    self.event_handler.on_progress(
                        current=matches_played,
                        total=self.max_matches,
                        message="Running Elo matches...",
                    )

                    if self.tournament:
                        self.tournament.record_match()
                        if self.tournament.should_advance_round():
                            if not self.tournament.advance_round():
                                break  # Tournament complete

                # Check early stopping
                if self.stability_checker:
                    if self.stability_checker.check(self.elo_candidates):
                        # Emit early stop event via progress
                        self.event_handler.on_progress(
                            current=matches_played,
                            total=self.max_matches,
                            message="Rankings stabilized - stopping early",
                        )
                        break
        finally:
            # Stop display if handler supports it
            if hasattr(self.event_handler, 'stop_elo_display'):
                self.event_handler.stop_elo_display(
                    candidates=self.elo_candidates,
                    final=True,
                )

        # Sort candidates by Elo rating (highest first)
        self.elo_candidates.sort(key=lambda x: x.elo, reverse=True)

        return self.elo_candidates
