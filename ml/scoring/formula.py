"""Combine similarity + macro fit + budget fit + prep-time fit into one score."""
import math

# Documented 6-Factor weights (from plan.pdf and test_scoring.py)
WEIGHT_MACRO = 0.30
WEIGHT_GOAL = 0.20
WEIGHT_PREF = 0.20
WEIGHT_FEEDBACK = 0.15
WEIGHT_DIVERSITY = 0.10
WEIGHT_PREP = 0.05

# 4-factor weights for candidate-level scoring (from Workflow Brief Section 6)
# 0.4 similarity, 0.3 macro_fit, 0.2 budget_fit, 0.1 prep_time_fit
WEIGHTS = {
    "similarity": 0.4,
    "macro_fit": 0.3,
    "budget_fit": 0.2,
    "prep_time_fit": 0.1,
}

# Validation: ensure 4-factor weights sum to 1.0 and are non-negative
assert all(w >= 0.0 for w in WEIGHTS.values()), "Weights must be non-negative"
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"


def _safe_float(val, default: float = 0.0) -> float:
    """Safely convert any input to float, handling None, NaN, inf, or negative values."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def macro_fit_score(item: dict, user_profile: dict) -> float:
    """
    Evaluates how closely item's calories match the per-meal calorie target (daily / 4).
    Safe on None, 0, NaN, and negative values. Output strictly bounded [0.0, 1.0].
    """
    raw_target = user_profile.get("target_calories", 2000)
    target_cal = _safe_float(raw_target, default=2000.0) / 4.0
    if target_cal <= 0.0:
        target_cal = 500.0

    raw_item_cal = item.get("calories", target_cal)
    item_cal = _safe_float(raw_item_cal, default=target_cal)
    if item_cal < 0.0:
        item_cal = 0.0

    diff = abs(item_cal - target_cal)
    score = 1.0 - (diff / target_cal)
    return max(0.0, min(1.0, score))


def budget_fit_score(item: dict, user_profile: dict) -> float:
    """
    Evaluates if item cost estimate fits within user's per-meal budget.
    Output strictly bounded [0.0, 1.0].
    """
    raw_budget = user_profile.get("budget_per_meal", 100.0)
    budget = _safe_float(raw_budget, default=100.0)
    if budget <= 0.0:
        budget = 100.0

    raw_cost = item.get("cost_estimate", budget)
    cost = _safe_float(raw_cost, default=budget)
    if cost <= budget:
        return 1.0

    excess = cost - budget
    score = 1.0 - (excess / budget)
    return max(0.0, min(1.0, score))


def prep_time_fit_score(item: dict, user_profile: dict) -> float:
    """
    Evaluates if item prep time is within user's prep time limit.
    Output strictly bounded [0.0, 1.0].
    """
    raw_limit = user_profile.get("prep_time_limit", 30.0)
    limit = _safe_float(raw_limit, default=30.0)
    if limit <= 0.0:
        limit = 30.0

    raw_prep = item.get("prep_time", limit)
    prep = _safe_float(raw_prep, default=limit)
    if prep <= limit:
        return 1.0

    excess = prep - limit
    score = 1.0 - (excess / limit)
    return max(0.0, min(1.0, score))


def compute_score(*args, **kwargs) -> any:
    """
    Overloaded scoring function:
    1) If called with 6 float arguments:
       compute_score(macro, goal, pref, feedback, diversity, prep) -> float
       Evaluates the 6 documented clinical/recommendation factors.
    2) If called with (item, user_profile, similarity):
       compute_score(item, user_profile, similarity) -> dict
       Returns {"final_score": ..., "similarity": ..., "macro_fit": ..., "budget_fit": ..., "prep_time_fit": ...}
    All scores strictly bounded [0.0, 1.0]. Safe on None, 0, NaN, negative.
    """
    if len(args) == 6 and not isinstance(args[0], dict):
        macro, goal, pref, feedback, diversity, prep = args
        for val, name in [
            (macro, "macro"),
            (goal, "goal"),
            (pref, "pref"),
            (feedback, "feedback"),
            (diversity, "diversity"),
            (prep, "prep"),
        ]:
            if not isinstance(val, (int, float)):
                raise ValueError(f"{name} score must be a number, got {val}")
            if val < 0.0 or val > 1.0:
                raise ValueError(f"{name} score must be between 0.0 and 1.0, got {val}")

        final = (
            WEIGHT_MACRO * macro
            + WEIGHT_GOAL * goal
            + WEIGHT_PREF * pref
            + WEIGHT_FEEDBACK * feedback
            + WEIGHT_DIVERSITY * diversity
            + WEIGHT_PREP * prep
        )
        return min(1.0, max(0.0, final))

    if len(args) >= 3 and isinstance(args[0], dict) and isinstance(args[1], dict):
        item, user_profile, raw_sim = args[0], args[1], args[2]
        similarity = max(0.0, min(1.0, _safe_float(raw_sim, 0.0)))
        macro = macro_fit_score(item, user_profile)
        budget = budget_fit_score(item, user_profile)
        prep = prep_time_fit_score(item, user_profile)

        weights = kwargs.get("weights", WEIGHTS)
        final = (
            weights["similarity"] * similarity
            + weights["macro_fit"] * macro
            + weights["budget_fit"] * budget
            + weights["prep_time_fit"] * prep
        )
        final = max(0.0, min(1.0, final))

        return {
            "final_score": final,
            "similarity": similarity,
            "macro_fit": macro,
            "budget_fit": budget,
            "prep_time_fit": prep,
        }

    raise ValueError("Invalid arguments passed to compute_score()")
