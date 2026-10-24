"""Combine similarity + macro fit + budget fit + prep-time fit into one score."""

# Documented 6-Factor weights (from plan.pdf and test_scoring.py)
WEIGHT_MACRO = 0.30
WEIGHT_GOAL = 0.20
WEIGHT_PREF = 0.20
WEIGHT_FEEDBACK = 0.15
WEIGHT_DIVERSITY = 0.10
WEIGHT_PREP = 0.05

# Legacy/alternate 4-factor dictionary weights for candidate-level scoring
WEIGHTS = {
    "similarity": 0.4,
    "macro_fit": 0.3,
    "budget_fit": 0.2,
    "prep_time_fit": 0.1,
}

def macro_fit_score(item: dict, user_profile: dict) -> float:
    target_cal = user_profile.get("target_calories", 2000) / 4  # per-meal target
    diff = abs(item.get("calories", target_cal) - target_cal)
    return max(0.0, 1 - diff / target_cal)

def budget_fit_score(item: dict, user_profile: dict) -> float:
    budget = user_profile.get("budget_per_meal", 100)
    cost = item.get("cost_estimate", budget)
    return max(0.0, 1 - max(0, cost - budget) / budget)

def prep_time_fit_score(item: dict, user_profile: dict) -> float:
    limit = user_profile.get("prep_time_limit", 30)
    prep = item.get("prep_time", limit)
    return max(0.0, 1 - max(0, prep - limit) / limit)

def compute_score(*args, **kwargs) -> any:
    """
    Overloaded scoring function:
    1) If called with 6 float arguments:
       compute_score(macro, goal, pref, feedback, diversity, prep) -> float
       Evaluates the 6 documented clinical/recommendation factors.
    2) If called with (item, user_profile, similarity):
       compute_score(item, user_profile, similarity) -> dict
       Returns {"final_score": ..., "similarity": ..., "macro_fit": ..., "budget_fit": ..., "prep_time_fit": ...}
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
        item, user_profile, similarity = args[0], args[1], args[2]
        macro = macro_fit_score(item, user_profile)
        budget = budget_fit_score(item, user_profile)
        prep = prep_time_fit_score(item, user_profile)

        final = (
            WEIGHTS["similarity"] * similarity
            + WEIGHTS["macro_fit"] * macro
            + WEIGHTS["budget_fit"] * budget
            + WEIGHTS["prep_time_fit"] * prep
        )

        return {
            "final_score": final,
            "similarity": similarity,
            "macro_fit": macro,
            "budget_fit": budget,
            "prep_time_fit": prep,
        }

    raise ValueError("Invalid arguments passed to compute_score()")

