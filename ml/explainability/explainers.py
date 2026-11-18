"""
DietSense ML — Recommendation Explanations (Phase 8D).

Priority 4: Recommendation explanations
- Explains why a meal was selected using actual scoring information.
- Shows relevant nutritional factors (macros and verified micronutrients).
- Discloses adaptive feedback adjustments and 7-day diversity penalties.
- Never fabricates metrics or claims factors not included in the scoring run.
"""

from typing import Dict, Any, List, Optional


def _format_nutrient_highlight(item: Dict[str, Any]) -> List[str]:
    """Extract verified nutritional highlights present in the item."""
    highlights = []

    # Protein
    prot = item.get("protein_g")
    if prot is not None:
        try:
            prot_f = float(prot)
            if prot_f >= 20.0:
                highlights.append(f"high protein ({round(prot_f)}g)")
            elif prot_f >= 12.0:
                highlights.append(f"balanced protein ({round(prot_f)}g)")
        except (ValueError, TypeError):
            pass

    # Fiber
    fiber = item.get("fiber_g")
    if fiber is not None:
        try:
            fiber_f = float(fiber)
            if fiber_f >= 6.0:
                highlights.append(f"rich in dietary fiber ({fiber_f:.1f}g)")
            elif fiber_f >= 3.0:
                highlights.append(f"provides dietary fiber ({fiber_f:.1f}g)")
        except (ValueError, TypeError):
            pass

    # Micronutrients dict (from verified SQLite food record)
    micros = item.get("micronutrients") or {}

    # Sodium (check top-level or in micronutrients)
    sodium = item.get("sodium_mg") if item.get("sodium_mg") is not None else micros.get("sodium_mg")
    if sodium is not None:
        try:
            sod_f = float(sodium)
            if sod_f <= 140.0:
                highlights.append(f"low sodium ({round(sod_f)}mg)")
        except (ValueError, TypeError):
            pass

    # Iron
    iron = item.get("iron_mg") if item.get("iron_mg") is not None else micros.get("iron_mg")
    if iron is not None:
        try:
            iron_f = float(iron)
            if iron_f >= 3.5:
                highlights.append(f"notable iron content ({iron_f:.1f}mg)")
        except (ValueError, TypeError):
            pass

    # Calcium
    calcium = item.get("calcium_mg") if item.get("calcium_mg") is not None else micros.get("calcium_mg")
    if calcium is not None:
        try:
            cal_f = float(calcium)
            if cal_f >= 150.0:
                highlights.append(f"calcium-rich ({round(cal_f)}mg)")
        except (ValueError, TypeError):
            pass

    return highlights


def generate_reason(item: dict, user_profile: dict, score_breakdown: dict) -> str:
    """
    Generate a concise, clinically grounded natural language explanation for why
    this candidate was recommended. Built exclusively from real scoring factors.
    """
    reasons: List[str] = []

    # 1. Dietary preference compliance
    diet = user_profile.get("dietary_pref") or user_profile.get("dietary_preference")
    if diet:
        reasons.append(f"matches your {diet} preference")

    # 2. Nutritional factors
    nutri_highlights = _format_nutrient_highlight(item)
    if nutri_highlights:
        reasons.append(", ".join(nutri_highlights))

    # 3. Macro target fit
    macro_fit = score_breakdown.get("macro_fit", 0.0)
    if macro_fit >= 0.85:
        reasons.append("aligns closely with your per-meal calorie target")
    elif macro_fit >= 0.70:
        reasons.append("fits your calorie allocation")

    # 4. Budget fit
    if score_breakdown.get("budget_fit", 0.0) >= 0.85:
        reasons.append("fits within your budget target")

    # 5. Prep time fit
    prep = item.get("prep_time")
    if prep is not None and score_breakdown.get("prep_time_fit", 0.0) >= 0.80:
        reasons.append(f"quick ~{prep} min prep time")

    # 6. Cuisine & Taste similarity
    if score_breakdown.get("similarity", 0.0) >= 0.55:
        reasons.append("matches your cuisine and flavor preferences")

    # 7. Adaptive feedback adjustments (Priority 2)
    adaptive_penalty = score_breakdown.get("adaptive_penalty", 0.0)
    if adaptive_penalty > 0.0:
        penalized_tags = score_breakdown.get("penalized_tags", [])
        if penalized_tags:
            tag_desc = ", ".join(penalized_tags)
            reasons.append(f"adjusted for previous skips on {tag_desc} (-{adaptive_penalty:.2f})")
        else:
            reasons.append(f"adjusted based on your meal skip history (-{adaptive_penalty:.2f})")

    affinity_boost = score_breakdown.get("affinity_boost", 0.0)
    if affinity_boost > 0.0:
        reasons.append(f"boosted from your positive meal adherence (+{affinity_boost:.2f})")

    # 8. Seven-day meal diversity (Priority 1)
    diversity_penalty = score_breakdown.get("diversity_penalty", 0.0)
    if diversity_penalty > 0.0:
        days_ago = score_breakdown.get("days_since_last")
        days_str = f"eaten {days_ago}d ago" if days_ago is not None else "recent repetition"
        reasons.append(f"7-day rotation diversity adjustment ({days_str}, -{diversity_penalty:.2f})")
    elif score_breakdown.get("diversity_status") == "fresh":
        reasons.append("adds meal variety to your 7-day plan")

    if not reasons:
        reasons.append("matches your core onboarding parameters")

    return "Recommended because it " + ", ".join(reasons) + "."


def generate_structured_explanation(
    item: Dict[str, Any],
    user_profile: Dict[str, Any],
    score_breakdown: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Priority 4: Structured Explanation Object for frontend inspection and transparency.
    """
    highlights = _format_nutrient_highlight(item)
    return {
        "summary": generate_reason(item, user_profile, score_breakdown),
        "primary_factor": (
            "High Protein Alignment" if any("protein" in h for h in highlights)
            else "Calorie Allocation Match" if score_breakdown.get("macro_fit", 0) >= 0.8
            else "Cuisine Preference"
        ),
        "nutrition_highlights": highlights,
        "scoring_factors": {
            "similarity": score_breakdown.get("similarity", 0.0),
            "macro_fit": score_breakdown.get("macro_fit", 0.0),
            "budget_fit": score_breakdown.get("budget_fit", 0.0),
            "prep_time_fit": score_breakdown.get("prep_time_fit", 0.0),
            "adaptive_penalty": score_breakdown.get("adaptive_penalty", 0.0),
            "affinity_boost": score_breakdown.get("affinity_boost", 0.0),
            "diversity_penalty": score_breakdown.get("diversity_penalty", 0.0),
            "final_score": score_breakdown.get("final_score", 0.0),
        },
        "diversity": {
            "status": score_breakdown.get("diversity_status", "fresh"),
            "days_since_last": score_breakdown.get("days_since_last"),
            "frequency_7d": score_breakdown.get("frequency_7d", 0),
            "penalty": score_breakdown.get("diversity_penalty", 0.0),
        },
        "micronutrients_available": {
            "fiber_g": item.get("fiber_g"),
            "sodium_mg": item.get("sodium_mg"),
            "calcium_mg": item.get("calcium_mg"),
            "iron_mg": item.get("iron_mg"),
        },
    }
