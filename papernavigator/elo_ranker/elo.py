"""Pure Elo rating calculations."""

import math

from papernavigator.elo_ranker.models import CandidateElo


def expected_score(elo_a: float, elo_b: float) -> float:
    """Calculate expected score for candidate A against candidate B.
    
    Uses the standard Elo formula: E_A = 1 / (1 + 10^((R_B - R_A) / 400))
    
    Args:
        elo_a: Elo rating of candidate A
        elo_b: Elo rating of candidate B
        
    Returns:
        Expected score (0.0 to 1.0) for candidate A
    """
    return 1.0 / (1.0 + math.pow(10.0, (elo_b - elo_a) / 400.0))


def update_elo(
    candidate_elo1: CandidateElo,
    candidate_elo2: CandidateElo,
    winner: int | None,
    k_factor: float = 32.0
) -> None:
    """Update Elo ratings after a match.
    
    Args:
        candidate_elo1: First candidate's Elo object
        candidate_elo2: Second candidate's Elo object
        winner: 1 if candidate1 won, 2 if candidate2 won, None for draw (0.5 each)
        k_factor: K-factor for Elo updates (default 32, typical for chess)
    """
    elo1 = candidate_elo1.elo
    elo2 = candidate_elo2.elo

    # Calculate expected scores
    expected1 = expected_score(elo1, elo2)
    expected2 = expected_score(elo2, elo1)

    # Determine actual scores and update W/L/D records
    if winner == 1:
        # Candidate 1 won
        actual1 = 1.0
        actual2 = 0.0
        candidate_elo1.wins += 1
        candidate_elo2.losses += 1
    elif winner == 2:
        # Candidate 2 won
        actual1 = 0.0
        actual2 = 1.0
        candidate_elo1.losses += 1
        candidate_elo2.wins += 1
    else:
        # Draw
        actual1 = 0.5
        actual2 = 0.5
        candidate_elo1.draws += 1
        candidate_elo2.draws += 1

    # Update ratings: R' = R + K * (S - E)
    candidate_elo1.elo = elo1 + k_factor * (actual1 - expected1)
    candidate_elo2.elo = elo2 + k_factor * (actual2 - expected2)
