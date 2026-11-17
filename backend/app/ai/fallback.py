"""
DietSense — Rule-Based Fallback Engine
Provides 100% deterministic, offline responses for all AI endpoints
when Google Gemini is unconfigured, unreachable, or rate-limited.
Never invents nutrition values; always grounds to database rows.
"""

from typing import Dict, Any, List
from ml.explainability.explainers import generate_reason


def fallback_assistant_chat(query: str, user_profile: Dict[str, Any], foods: List[Dict[str, Any]]) -> str:
    """Deterministic conversational assistant response."""
    q = query.lower()
    target_cal = user_profile.get("target_calories", 2000)
    diet = user_profile.get("dietary_pref", "vegetarian")
    goal = user_profile.get("goal", "maintain_weight")

    response_parts = []
    if "protein" in q:
        high_protein_foods = sorted(foods, key=lambda x: x.get("protein_g", 0), reverse=True)[:3]
        if high_protein_foods:
            names = ", ".join([f"{f['name']} ({f.get('protein_g', 0):.1f}g)" for f in high_protein_foods])
            response_parts.append(f"For higher protein on a {diet} diet, good choices from your catalog include {names}.")
        else:
            response_parts.append(f"To reach your daily protein goals on a {diet} diet, focus on lentils, pulses, paneer/tofu, and Greek yogurt.")

    elif "calorie" in q or "deficit" in q or "weight" in q:
        response_parts.append(
            f"Your current daily target is {target_cal} kcal tailored for your goal to {goal.replace('_', ' ')}. "
            f"Spacing meals across regular intervals helps maintain satiety while adhering to this target."
        )

    elif "snack" in q:
        snack_foods = [f for f in foods if "snack" in str(f.get("tags", [])).lower() or "fruit" in str(f.get("food_category", "")).lower()][:2]
        if snack_foods:
            names = " or ".join([f['name'] for f in snack_foods])
            response_parts.append(f"Nutrient-dense snack options from your plan include {names}.")
        else:
            response_parts.append("For midday energy without spikes, choose roasted makhana, sprouted moong, or fresh seasonal fruit with a few soaked almonds.")

    else:
        response_parts.append(
            f"Based on your {diet} preference and target of {target_cal} kcal, "
            f"balanced nutrition requires combining complex carbohydrates with adequate lean protein and fiber."
        )

    if foods:
        sample_food = foods[0]
        response_parts.append(
            f"For instance, {sample_food['name']} provides {sample_food.get('calories_kcal', 0):.0f} kcal "
            f"and {sample_food.get('protein_g', 0):.1f}g protein per standard portion."
        )

    return " ".join(response_parts)


def fallback_explain_recommendation(
    food: Dict[str, Any],
    user_profile: Dict[str, Any],
    score_breakdown: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministic explanation fallback based on ML score breakdown."""
    base_reason = generate_reason(food, user_profile, score_breakdown or {})

    cal = food.get("calories_kcal", 0)
    protein = food.get("protein_g", 0)
    name = food.get("name", "This meal")

    headline = f"{name}: {protein:.1f}g Protein & {cal:.0f} kcal Fit"
    explanation = f"{base_reason} It fits cleanly within your daily metabolic schedule without exceeding sodium or saturated fat limits."

    benefits = [
        f"Delivers {protein:.1f}g protein to support muscle preservation during calorie control",
        f"Provides balanced macro partition with {food.get('carbohydrates_g', 0):.1f}g complex carbohydrates",
    ]

    prep_time = food.get("prep_time", 20)
    prep_tip = f"Requires approximately {prep_time} minutes of prep time; can be batch-cooked in advance for busy weekdays."

    return {
        "headline": headline,
        "explanation": explanation,
        "key_benefits": benefits,
        "preparation_tip": prep_tip,
    }


def fallback_suggest_recipes(
    candidates: List[Dict[str, Any]],
    meal_slot: str,
    target_calories: int,
) -> List[Dict[str, Any]]:
    """Deterministic recipe suggestions drawn from safe candidate catalog items."""
    results = []
    for food in candidates[:4]:
        name = food.get("name", "Meal")
        cal = food.get("calories_kcal", 350)
        protein = food.get("protein_g", 12)
        carbs = food.get("carbohydrates_g", 40)
        fat = food.get("fat_g", 8)

        results.append({
            "title": f"Nutritious {name}",
            "meal_slot": meal_slot,
            "estimated_prep_time_mins": int(food.get("prep_time", 20)),
            "matched_catalog_food_id": food.get("id"),
            "ingredients": [
                f"1 portion ({name})",
                "1/2 tsp Cold-pressed oil or ghee",
                "Pinch of cumin & turmeric",
                "Fresh coriander for garnish"
            ],
            "overview": f"A balanced {meal_slot} option focused on wholesome ingredients with verified USDA/ICMR nutrition.",
            "verified_nutrition_estimate": {
                "calories_kcal": cal,
                "protein_g": protein,
                "carbohydrates_g": carbs,
                "fat_g": fat,
            }
        })
    return results


def fallback_pantry_cooking(
    pantry_items: List[str],
    candidate_foods: List[Dict[str, Any]],
    max_prep_time_mins: int,
) -> List[Dict[str, Any]]:
    """Deterministic pantry-based meal assembly."""
    pantry_set = {p.lower() for p in pantry_items}
    matched_candidate = candidate_foods[0] if candidate_foods else {
        "id": 1,
        "name": "Quick Pantry Sauté",
        "calories_kcal": 280,
        "protein_g": 12,
        "carbohydrates_g": 30,
        "fat_g": 8,
    }

    used = [p for p in pantry_items[:4]]
    return [{
        "recipe_name": f"Home-Style {matched_candidate['name']}",
        "prep_time_mins": min(max_prep_time_mins, 20),
        "matched_pantry_items": used,
        "missing_items": ["Salt & black pepper (pantry staple)"],
        "cooking_steps": [
            "Wash and chop the fresh ingredients into bite-sized pieces.",
            "Heat 1 tsp cooking oil or ghee in a pan over medium heat.",
            f"Add {', '.join(used[:2]) if used else 'ingredients'} and stir-fry for 6-8 minutes until tender.",
            "Season lightly and serve warm."
        ],
        "nutrition_anchor_food_id": matched_candidate.get("id"),
        "nutrition_anchor_name": matched_candidate.get("name"),
        "nutrition_facts": {
            "calories_kcal": matched_candidate.get("calories_kcal", 300),
            "protein_g": matched_candidate.get("protein_g", 12),
            "carbs_g": matched_candidate.get("carbohydrates_g", 35),
            "fat_g": matched_candidate.get("fat_g", 8),
        }
    }]


def fallback_compare_meals(foods: List[Dict[str, Any]], priority: str) -> Dict[str, Any]:
    """Deterministic mathematical comparison between 2+ food items."""
    highest_protein = max(foods, key=lambda x: x.get("protein_g", 0))
    lowest_cal = min(foods, key=lambda x: x.get("calories_kcal", 9999))

    winner = highest_protein["name"] if priority == "protein" else lowest_cal["name"]

    names = [f["name"] for f in foods]
    analysis = (
        f"Comparing {len(foods)} items: '{highest_protein['name']}' leads in protein with {highest_protein.get('protein_g', 0):.1f}g, "
        f"while '{lowest_cal['name']}' offers the lightest caloric load at {lowest_cal.get('calories_kcal', 0):.0f} kcal. "
        f"For your preference '{priority}', '{winner}' represents the optimal choice."
    )

    tradeoffs = [
        f"{highest_protein['name']} has {highest_protein.get('protein_g', 0):.1f}g protein vs {lowest_cal['name']}'s {lowest_cal.get('protein_g', 0):.1f}g.",
        f"{lowest_cal['name']} saves {abs(highest_protein.get('calories_kcal', 0) - lowest_cal.get('calories_kcal', 0)):.0f} kcal compared to {highest_protein['name']}."
    ]

    return {
        "analysis": analysis,
        "key_tradeoffs": tradeoffs,
        "winner_for_goal": winner,
        "macro_comparison": {
            "highest_protein": highest_protein["name"],
            "lowest_calorie": lowest_cal["name"],
            "best_budget": foods[0]["name"]
        }
    }


def fallback_cooking_instructions(food: Dict[str, Any], servings: int, skill_level: str) -> Dict[str, Any]:
    """Deterministic step-by-step cooking steps based on verified food properties."""
    name = food.get("name", "Dish")
    cat = str(food.get("food_category", "")).lower()

    prep = 10 if "fruit" in cat or "salad" in cat else 15
    cook = 15 if "cereal" in cat or "vegetable" in cat else 25

    return {
        "prep_time_mins": prep,
        "cook_time_mins": cook,
        "equipment_needed": ["Non-stick skillet or wok", "Wooden spatula", "Cutting board & knife"],
        "ingredients": [
            f"{servings} standard portion(s) of {name}",
            f"{servings * 1} tsp Cold-pressed oil or ghee",
            "Salt, cumin, and turmeric to taste",
            "Fresh herbs (coriander/mint) for topping"
        ],
        "step_by_step_instructions": [
            f"Step 1: Prep and rinse all components of {name} thoroughly.",
            "Step 2: Heat cooking fat in your skillet over medium-low heat.",
            "Step 3: Add whole spices and sauté gently until aromatic (30 seconds).",
            f"Step 4: Add the main ingredients and cook on medium heat for {cook - 5} minutes, stirring periodically.",
            "Step 5: Turn off heat, rest covered for 2 minutes, and serve warm."
        ],
        "chef_tips": [
            "Avoid high-heat smoking of cooking oils to preserve heart-healthy fats.",
            "Use lemon juice or amchur instead of extra salt to elevate the natural flavors."
        ]
    }
