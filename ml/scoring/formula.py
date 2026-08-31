"""
DietSense — Hybrid Recommendation Scoring Formula

Source: plan.pdf — Section 1 (Executive Overview & Architectural Principles)

score = (
    0.30 × macro_match_score
  + 0.20 × goal_alignment_score
  + 0.20 × user_pref_score
  + 0.15 × feedback_history_score
  + 0.10 × diversity_score
  + 0.05 × prep_complexity_score
)

All sub-scores MUST be normalized to [0, 1] before calling compute_score().

Phase 1: Constants and interface defined.
Phase 6: Full scoring logic implemented (Rule-Based Rec Engine).
Phase 7: Adaptive re-ranking from user feedback.
"""

# ─── Scoring Weight Constants ─────────────────────────────────────────────────
WEIGHT_MACRO: float = 0.30
"""How closely the recipe's macros match the user's daily calorie/macro targets."""

WEIGHT_GOAL: float = 0.20
"""Alignment with the user's weight goal (lose_weight, maintain_weight, gain_weight)."""

WEIGHT_PREF: float = 0.20
"""Learned preference score from Ridge Regression on cuisine/ingredient history."""

WEIGHT_FEEDBACK: float = 0.15
"""Weighted average of the user's past ratings on similar meals."""

WEIGHT_DIVERSITY: float = 0.10
"""Penalises repetition of recipes seen in the past N days (N=7 default)."""

WEIGHT_PREP: float = 0.05
"""
Prep complexity score — simpler prep is preferred on weekdays.
Computed from recipe.prep_time_mins + cook_time_mins vs. user's max_prep_time setting.
"""

# Sanity check: weights must sum to 1.0
_TOTAL_WEIGHT = WEIGHT_MACRO + WEIGHT_GOAL + WEIGHT_PREF + WEIGHT_FEEDBACK + WEIGHT_DIVERSITY + WEIGHT_PREP
assert abs(_TOTAL_WEIGHT - 1.0) < 1e-9, f"Scoring weights must sum to 1.0, got {_TOTAL_WEIGHT}"


# ─── WHO Dietary Reference Bounds ────────────────────────────────────────────
# Source: WHO Healthy Diet Fact Sheet (2026-01-26)
# Used to compute macro_match_score and goal_alignment_score.

WHO_CARB_PCT_MIN: float = 0.45
WHO_CARB_PCT_MAX: float = 0.75
WHO_PROTEIN_PCT_MIN: float = 0.10
WHO_PROTEIN_PCT_MAX: float = 0.15
WHO_FAT_PCT_MIN: float = 0.15
WHO_FAT_PCT_MAX: float = 0.30
WHO_SATURATED_FAT_PCT_MAX: float = 0.10
WHO_TRANS_FAT_PCT_MAX: float = 0.01
WHO_FREE_SUGAR_PCT_MAX: float = 0.10
WHO_SALT_G_PER_DAY_MAX: float = 5.0
WHO_SODIUM_G_PER_DAY_MAX: float = 2.0
WHO_FIBER_G_PER_DAY_MIN: float = 25.0
WHO_FRUIT_VEG_G_PER_DAY_MIN: float = 400.0
WHO_POTASSIUM_MG_PER_DAY_MIN: float = 3510.0


# ─── Scoring Interface ────────────────────────────────────────────────────────

def compute_score(
    macro_score: float,
    goal_score: float,
    pref_score: float,
    feedback_score: float,
    diversity_score: float,
    prep_score: float,
) -> float:
    """
    Compute the weighted hybrid recommendation score for a single recipe candidate.

    All input scores MUST be pre-normalized to [0, 1].
    Returns a float in [0, 1].

    Implementation note:
    - macro_score: computed in ml/scoring/macro_scorer.py (Phase 6)
    - goal_score: computed from user.goal vs. recipe calorie density (Phase 6)
    - pref_score: output of Ridge Regression preference model (Phase 6)
    - feedback_score: average of user_feedback.rating for similar recipes (Phase 7)
    - diversity_score: 1.0 if recipe unseen in 7 days, decays if recently served (Phase 6)
    - prep_score: inverse of normalized prep+cook time (Phase 6)
    """
    _validate_scores(macro_score, goal_score, pref_score, feedback_score, diversity_score, prep_score)

    return (
        WEIGHT_MACRO     * macro_score     +
        WEIGHT_GOAL      * goal_score      +
        WEIGHT_PREF      * pref_score      +
        WEIGHT_FEEDBACK  * feedback_score  +
        WEIGHT_DIVERSITY * diversity_score +
        WEIGHT_PREP      * prep_score
    )


def _validate_scores(*scores: float) -> None:
    """Validate that all sub-scores are in [0, 1]."""
    for score in scores:
        if not (0.0 <= score <= 1.0):
            raise ValueError(
                f"All sub-scores must be normalized to [0, 1]. Got: {score}"
            )
