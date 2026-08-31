"""
Phase 1 — Scoring formula sanity tests.
Verifies weight constants and compute_score() interface before ML implementation.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from ml.scoring.formula import (
    WEIGHT_MACRO, WEIGHT_GOAL, WEIGHT_PREF,
    WEIGHT_FEEDBACK, WEIGHT_DIVERSITY, WEIGHT_PREP,
    compute_score,
)


def test_weights_sum_to_one():
    """All scoring weights must sum to exactly 1.0."""
    total = WEIGHT_MACRO + WEIGHT_GOAL + WEIGHT_PREF + WEIGHT_FEEDBACK + WEIGHT_DIVERSITY + WEIGHT_PREP
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"


def test_weight_values():
    """Weights must match the specification in plan.pdf."""
    assert WEIGHT_MACRO == 0.30
    assert WEIGHT_GOAL == 0.20
    assert WEIGHT_PREF == 0.20
    assert WEIGHT_FEEDBACK == 0.15
    assert WEIGHT_DIVERSITY == 0.10
    assert WEIGHT_PREP == 0.05


def test_compute_score_perfect():
    """All sub-scores at 1.0 should return 1.0."""
    score = compute_score(1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert abs(score - 1.0) < 1e-9


def test_compute_score_zero():
    """All sub-scores at 0.0 should return 0.0."""
    score = compute_score(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert score == 0.0


def test_compute_score_bounds():
    """Score must stay within [0, 1] for valid inputs."""
    score = compute_score(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    assert 0.0 <= score <= 1.0


def test_compute_score_rejects_out_of_range():
    """Sub-scores outside [0, 1] must raise ValueError."""
    with pytest.raises(ValueError):
        compute_score(1.5, 0.5, 0.5, 0.5, 0.5, 0.5)

    with pytest.raises(ValueError):
        compute_score(0.5, -0.1, 0.5, 0.5, 0.5, 0.5)
