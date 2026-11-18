"""
DietSense ML — Recommender Engine Orchestrator (Phase 8D).

Orchestrates:
1. Safety Gate (non-negotiable clinical exclusion of allergen & dietary conflicts).
2. TF-IDF & Cosine Similarity vectorizer against user profile preferences.
3. Multi-factor Scoring (calories/macro fit, budget fit, prep-time fit).
4. Adaptive Feedback Layer with logarithmic damping to prevent unstable scoring swings.
5. Seven-Day Meal Diversity Model to prevent repetitive recommendations.
6. Ingredient-aware Pantry Availability Bonus (+0.05 post-safety).
7. Clinically grounded Explainability (reason string + structured factor attribution).
"""

from typing import List, Dict, Any, Optional
from ml.scoring.safety_gate import filter_safe
from ml.recommendation.vectorizer import get_similarity
from ml.scoring.formula import compute_score
from ml.explainability.explainers import generate_reason, generate_structured_explanation
from ml.adaptive.reweight import (
    get_user_penalties,
    apply_adaptive_and_diversity,
)


def recommend(
    user_profile: dict,
    candidates: list[dict],
    meal_logs: list[dict] = None,
    top_n: int = 5,
    pantry_items: list[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filters candidates through safety gate, computes similarity, scores candidates,
    applies adaptive feedback penalties/affinities and seven-day diversity decay,
    applies pantry availability bonus, attaches explainability reason,
    and returns top_n ranked recommendations.

    Strictly preserves:
    - Non-negotiable safety gate (unsafe foods are excluded before any scoring).
    - Stable scoring (clamped in [0.0, 1.0] with logarithmic dampening).
    - Verified nutritional values.
    """
    # 1. Validate top_n
    try:
        top_n = int(top_n)
        if top_n <= 0:
            top_n = 5
    except (ValueError, TypeError):
        top_n = 5

    # 2. Strict Safety Gate (Applied FIRST — Unsafe items are eliminated)
    safe_candidates = filter_safe(candidates, user_profile)
    if not safe_candidates:
        return []

    # 3. Compute TF-IDF similarities
    similarities = get_similarity(user_profile, safe_candidates)

    # 4. Compute penalties & diversity context
    logs = meal_logs or []
    penalties = get_user_penalties(logs)

    # Normalise pantry items once for case-insensitive matching
    pantry_set = {p.lower() for p in pantry_items} if pantry_items else set()

    scored = []
    for item, sim in zip(safe_candidates, similarities):
        # Base formula score (similarity, macro_fit, budget_fit, prep_time_fit)
        breakdown = compute_score(item, user_profile, sim)

        # Apply adaptive feedback (Priority 2) and 7-day diversity (Priority 1)
        breakdown = apply_adaptive_and_diversity(breakdown, item, logs, penalties)

        # Apply pantry availability bonus (post-safety, post-scoring)
        pantry_matched = False
        if pantry_set:
            food_words = {w.lower() for w in item.get("name", "").split()}
            if food_words & pantry_set:
                pantry_matched = True
                breakdown["final_score"] = min(breakdown["final_score"] + 0.05, 1.0)
                breakdown["final_score"] = max(breakdown["final_score"], 0.0)

        # Generate explanations (Priority 4)
        reason = generate_reason(item, user_profile, breakdown)
        if pantry_matched:
            reason += " Pantry match: ingredients available at home."

        structured_exp = generate_structured_explanation(item, user_profile, breakdown)

        scored.append({
            "item": item,
            "score": breakdown["final_score"],
            "breakdown": breakdown,
            "reason": reason,
            "explanation": structured_exp,
        })

    # Sort descending by final score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
