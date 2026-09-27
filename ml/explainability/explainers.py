"""Turn a score breakdown into a plain-language reason string."""

def generate_reason(item: dict, user_profile: dict, score_breakdown: dict) -> str:
    reasons = []
    diet = user_profile.get("dietary_pref")
    if diet:
        reasons.append(f"matches your {diet} preference")
    
    if score_breakdown["budget_fit"] >= 0.8:
        reasons.append("fits your budget")
        
    prep = item.get("prep_time")
    if prep is not None:
        reasons.append(f"~{prep} min prep")
        
    if score_breakdown["macro_fit"] >= 0.8:
        reasons.append("matches your calorie target well")
        
    if score_breakdown["similarity"] >= 0.6:
        reasons.append("similar to meals you've rated positively")
        
    if not reasons:
        reasons.append("a reasonable match based on your profile")
        
    return "Recommended because it " + ", ".join(reasons) + "."
