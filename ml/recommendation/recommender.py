"""Orchestrator: the one function the API will call."""
from ml.scoring.safety_gate import filter_safe
from ml.recommendation.vectorizer import get_similarity
from ml.scoring.formula import compute_score
from ml.explainability.explainers import generate_reason
from ml.adaptive.reweight import get_user_penalties, apply_penalties

def recommend(user_profile: dict, candidates: list[dict], meal_logs: list[dict] = None, top_n: int = 5):
    safe_candidates = filter_safe(candidates, user_profile)
    if not safe_candidates:
        return []
        
    similarities = get_similarity(user_profile, safe_candidates)
    penalties = get_user_penalties(meal_logs or [])
    
    scored = []
    for item, sim in zip(safe_candidates, similarities):
        breakdown = compute_score(item, user_profile, sim)
        breakdown = apply_penalties(breakdown, item, penalties)
        reason = generate_reason(item, user_profile, breakdown)
        
        scored.append({
            "item": item,
            "score": breakdown["final_score"],
            "breakdown": breakdown,
            "reason": reason
        })
        
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
