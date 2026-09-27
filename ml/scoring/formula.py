"""Combine similarity + macro fit + budget fit + prep-time fit into one score."""

WEIGHTS = {"similarity": 0.4, "macro_fit": 0.3, "budget_fit": 0.2, "prep_time_fit": 0.1}

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

def compute_score(item: dict, user_profile: dict, similarity: float) -> dict:
    """Returns the final weighted score PLUS each component (for explainability)."""
    macro = macro_fit_score(item, user_profile)
    budget = budget_fit_score(item, user_profile)
    prep = prep_time_fit_score(item, user_profile)
    
    final = (
        WEIGHTS["similarity"] * similarity +
        WEIGHTS["macro_fit"] * macro +
        WEIGHTS["budget_fit"] * budget +
        WEIGHTS["prep_time_fit"] * prep
    )
    
    return {
        "final_score": final,
        "similarity": similarity,
        "macro_fit": macro,
        "budget_fit": budget,
        "prep_time_fit": prep,
    }
