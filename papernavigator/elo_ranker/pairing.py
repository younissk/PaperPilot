"""Pairing strategies for Elo ranking matches."""

import random
from typing import Protocol

from papernavigator.elo_ranker.models import CandidateElo


class PairingStrategy(Protocol):
    """Protocol for pairing strategies."""

    def select_pairs(
        self,
        candidates: list[CandidateElo],
        n_pairs: int
    ) -> list[tuple[CandidateElo, CandidateElo]]:
        """Select pairs of candidates for matches.
        
        Args:
            candidates: List of candidates with Elo ratings
            n_pairs: Number of pairs to select
            
        Returns:
            List of (candidate1, candidate2) tuples
        """
        ...


class RandomPairing:
    """Random pairing strategy - selects pairs randomly."""

    def select_pairs(
        self,
        candidates: list[CandidateElo],
        n_pairs: int
    ) -> list[tuple[CandidateElo, CandidateElo]]:
        """Select random pairs of candidates.
        
        Ensures pairs are unique and candidates don't match themselves.
        """
        if len(candidates) < 2:
            return []

        pairs = []
        used_indices = set()

        # Create list of available indices
        available = list(range(len(candidates)))

        while len(pairs) < n_pairs and len(available) >= 2:
            # Select two random indices
            idx1, idx2 = random.sample(available, 2)

            c1 = candidates[idx1]
            c2 = candidates[idx2]

            # Ensure they're different papers
            if c1.candidate.paper_id != c2.candidate.paper_id:
                pairs.append((c1, c2))
                # Remove used indices
                available.remove(idx1)
                if idx2 in available:
                    available.remove(idx2)

        return pairs


class SwissPairing:
    """Swiss-style pairing - pairs candidates with similar Elo ratings.
    
    This produces more informative matches by pairing papers that are
    close in rating, similar to chess tournament pairing.
    """

    def select_pairs(
        self,
        candidates: list[CandidateElo],
        n_pairs: int
    ) -> list[tuple[CandidateElo, CandidateElo]]:
        """Select pairs based on Elo proximity.
        
        Sorts candidates by Elo and pairs adjacent candidates.
        """
        if len(candidates) < 2:
            return []

        # Sort by Elo (highest first)
        sorted_candidates = sorted(candidates, key=lambda c: c.elo, reverse=True)

        pairs = []
        used = set()

        for i, c1 in enumerate(sorted_candidates):
            if c1.candidate.paper_id in used:
                continue

            # Find closest unused neighbor
            for j in range(i + 1, len(sorted_candidates)):
                c2 = sorted_candidates[j]
                if c2.candidate.paper_id not in used:
                    pairs.append((c1, c2))
                    used.update({c1.candidate.paper_id, c2.candidate.paper_id})
                    break

            if len(pairs) >= n_pairs:
                break

        return pairs
