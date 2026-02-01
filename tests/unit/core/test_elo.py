"""Unit tests for ELO rating calculations."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from papernavigator.elo_ranker.elo import expected_score, update_elo
from papernavigator.elo_ranker.models import CandidateElo
from papernavigator.models import EdgeType, SnowballCandidate

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


def make_candidate_elo(elo: float = 1500.0) -> CandidateElo:
    """Factory to create a CandidateElo for testing."""
    candidate = SnowballCandidate(
        paper_id="test-paper",
        title="Test Paper",
        abstract="Test abstract",
        year=2024,
        citation_count=100,
        influential_citation_count=10,
        discovered_from=None,
        edge_type=EdgeType.SEED,
        depth=0,
    )
    return CandidateElo(candidate=candidate, elo=elo)


class TestExpectedScore:
    """Tests for expected_score function."""

    def test_equal_ratings_gives_half(self):
        """Equal ratings should give expected score of 0.5."""
        result = expected_score(1500, 1500)
        assert result == pytest.approx(0.5)

    def test_higher_rating_gives_higher_expected(self):
        """Higher rated player has higher expected score."""
        result = expected_score(1600, 1400)
        assert result > 0.5
        assert result < 1.0

    def test_lower_rating_gives_lower_expected(self):
        """Lower rated player has lower expected score."""
        result = expected_score(1400, 1600)
        assert result < 0.5
        assert result > 0.0

    def test_400_point_difference(self):
        """400 point difference gives ~0.91 expected score."""
        result = expected_score(1900, 1500)
        assert result == pytest.approx(0.909, rel=0.01)

    def test_symmetry(self):
        """Expected scores are symmetric (sum to 1)."""
        e1 = expected_score(1600, 1400)
        e2 = expected_score(1400, 1600)
        assert e1 + e2 == pytest.approx(1.0)

    @given(
        elo_a=st.floats(min_value=100, max_value=3000),
        elo_b=st.floats(min_value=100, max_value=3000)
    )
    @settings(max_examples=100)
    def test_expected_score_bounds(self, elo_a, elo_b):
        """Property test: expected score is always between 0 and 1."""
        result = expected_score(elo_a, elo_b)
        assert 0.0 < result < 1.0

    @given(
        elo_a=st.floats(min_value=100, max_value=3000),
        elo_b=st.floats(min_value=100, max_value=3000)
    )
    @settings(max_examples=100)
    def test_expected_scores_sum_to_one(self, elo_a, elo_b):
        """Property test: expected scores always sum to 1."""
        e1 = expected_score(elo_a, elo_b)
        e2 = expected_score(elo_b, elo_a)
        assert e1 + e2 == pytest.approx(1.0)


class TestUpdateElo:
    """Tests for update_elo function."""

    def test_winner_gains_loser_loses(self):
        """Winner gains rating, loser loses rating."""
        c1 = make_candidate_elo(1500)
        c2 = make_candidate_elo(1500)

        update_elo(c1, c2, winner=1)

        assert c1.elo > 1500
        assert c2.elo < 1500

    def test_equal_rating_equal_change(self):
        """Equal ratings result in symmetric changes."""
        c1 = make_candidate_elo(1500)
        c2 = make_candidate_elo(1500)

        update_elo(c1, c2, winner=1, k_factor=32)

        # With equal ratings, winner gains half of k_factor
        assert c1.elo == pytest.approx(1516, rel=0.01)
        assert c2.elo == pytest.approx(1484, rel=0.01)

    def test_upset_gives_larger_change(self):
        """Lower rated player winning gives larger rating change."""
        c1 = make_candidate_elo(1400)  # lower rated
        c2 = make_candidate_elo(1600)  # higher rated

        old_c1 = c1.elo
        update_elo(c1, c2, winner=1)

        gain = c1.elo - old_c1
        # Upset should give more than 16 points (half k-factor)
        assert gain > 16

    def test_draw_minimal_change_for_equal(self):
        """Draw between equal ratings gives no change."""
        c1 = make_candidate_elo(1500)
        c2 = make_candidate_elo(1500)

        update_elo(c1, c2, winner=None)  # Draw

        assert c1.elo == pytest.approx(1500)
        assert c2.elo == pytest.approx(1500)

    def test_draw_adjusts_unequal_ratings(self):
        """Draw between unequal ratings moves them closer."""
        c1 = make_candidate_elo(1600)
        c2 = make_candidate_elo(1400)

        update_elo(c1, c2, winner=None)  # Draw

        # Higher rated loses points, lower rated gains
        assert c1.elo < 1600
        assert c2.elo > 1400

    def test_updates_win_loss_draw_records(self):
        """Win/loss/draw records are updated correctly."""
        c1 = make_candidate_elo()
        c2 = make_candidate_elo()

        # Test win
        update_elo(c1, c2, winner=1)
        assert c1.wins == 1
        assert c2.losses == 1

        # Test loss (c1 loses this time)
        update_elo(c1, c2, winner=2)
        assert c1.losses == 1
        assert c2.wins == 1

        # Test draw
        update_elo(c1, c2, winner=None)
        assert c1.draws == 1
        assert c2.draws == 1

    def test_k_factor_affects_magnitude(self):
        """Higher k-factor gives larger rating changes."""
        c1_low_k = make_candidate_elo(1500)
        c2_low_k = make_candidate_elo(1500)
        update_elo(c1_low_k, c2_low_k, winner=1, k_factor=16)

        c1_high_k = make_candidate_elo(1500)
        c2_high_k = make_candidate_elo(1500)
        update_elo(c1_high_k, c2_high_k, winner=1, k_factor=64)

        low_k_change = c1_low_k.elo - 1500
        high_k_change = c1_high_k.elo - 1500

        assert high_k_change > low_k_change
        assert high_k_change == pytest.approx(4 * low_k_change)

    @given(
        elo1=st.floats(min_value=500, max_value=2500),
        elo2=st.floats(min_value=500, max_value=2500),
        winner=st.sampled_from([1, 2, None]),
        k_factor=st.floats(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_total_elo_conserved(self, elo1, elo2, winner, k_factor):
        """Property test: total ELO is conserved after update."""
        c1 = make_candidate_elo(elo1)
        c2 = make_candidate_elo(elo2)
        total_before = c1.elo + c2.elo

        update_elo(c1, c2, winner, k_factor)

        total_after = c1.elo + c2.elo
        assert total_after == pytest.approx(total_before, rel=1e-10)


class TestCandidateEloModel:
    """Tests for CandidateElo model."""

    def test_default_values(self):
        """CandidateElo has correct defaults."""
        candidate = SnowballCandidate(
            paper_id="test",
            title="Test",
            edge_type=EdgeType.SEED,
            depth=0,
        )
        elo = CandidateElo(candidate=candidate)

        assert elo.elo == 1500.0
        assert elo.wins == 0
        assert elo.losses == 0
        assert elo.draws == 0

    def test_custom_initial_elo(self):
        """CandidateElo can have custom initial rating."""
        candidate = SnowballCandidate(
            paper_id="test",
            title="Test",
            edge_type=EdgeType.SEED,
            depth=0,
        )
        elo = CandidateElo(candidate=candidate, elo=2000.0)

        assert elo.elo == 2000.0
