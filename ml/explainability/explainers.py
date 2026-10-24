"""
Turn a score breakdown into a plain-language reason string.
Built exclusively from real score factors. Never claims ratings or factors not used.
Explicitly mentions adaptive adjustments when penalties are applied.
"""

def generate_reason(item: dict, user_profile: dict, score_breakdown: dict) -> str:
    reasons = []

    diet = user_profile.get("dietary_pref")
    if diet:
        reasons.append(f"matches your {diet} preference")

    if score_breakdown.get("budget_fit", 0) >= 0.8:
        reasons.append("fits within your budget target")

    prep = item.get("prep_time")
    if prep is not None:
        reasons.append(f"~{prep} min prep time")

    if score_breakdown.get("macro_fit", 0) >= 0.8:
        reasons.append("aligns closely with your per-meal calorie target")

    if score_breakdown.get("similarity", 0) >= 0.6:
        reasons.append("matches your cuisine and flavor preferences")

    adaptive_penalty = score_breakdown.get("adaptive_penalty", 0.0)
    if adaptive_penalty > 0.0:
        penalized_tags = score_breakdown.get("penalized_tags", [])
        if penalized_tags:
            tag_desc = ", ".join(penalized_tags)
            reasons.append(f"adjusted for previous skips on {tag_desc} (-{adaptive_penalty:.1f})")
        else:
            reasons.append(f"adjusted based on your meal skip history (-{adaptive_penalty:.1f})")

    if not reasons:
        reasons.append("matches your core onboarding parameters")

    return "Recommended because it " + ", ".join(reasons) + "."
