"""Data models for Elo ranking system."""

from typing import Literal

from pydantic import BaseModel

from papernavigator.models import SnowballCandidate


class CandidateElo(BaseModel):
    """Model for tracking a candidate's Elo rating."""
    candidate: SnowballCandidate
    elo: float
    wins: int = 0
    losses: int = 0
    draws: int = 0


class MatchResult(BaseModel):
    """Result of a single match between two papers."""
    paper1_title: str
    paper2_title: str
    winner: int | None  # 1, 2, or None for draw
    reason: str = ""


class RankerConfig(BaseModel):
    """Configuration for Elo ranking system."""
    initial_elo: float = 1500.0
    k_factor: float = 32.0

    # Pairing
    calibration_matches: int = 50  # Random before switching to Swiss
    pairing_strategy: Literal["random", "swiss"] = "swiss"

    # Stopping
    max_matches: int | None = None  # None = auto (len * 3)
    early_stop_enabled: bool = True
    early_stop_top_k: int = 30
    early_stop_threshold: float = 0.9
    early_stop_check_interval: int = 50

    # Tournament rounds (alternative to stability)
    tournament_mode: bool = False
    tournament_rounds: list[tuple[int, int]] = [(0, 50), (80, 100), (40, 100)]

    # Concurrency
    batch_size: int = 10
    concurrency: int = 5

    # Display
    interactive: bool = True
