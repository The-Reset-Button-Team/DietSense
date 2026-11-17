"""
DietSense — Gemini System Instructions & Prompt Templates
Enforces clinical grounding, strict adherence to USDA/ICMR-NIN nutrition facts,
hard safety bounds, and medical non-diagnosis invariants.
"""

SYSTEM_INSTRUCTION_CORE = """
You are DietSense AI, an intelligent, evidence-based nutrition assistant.
Your role is to explain meal choices, suggest culinary instructions, and offer practical eating tips.

NON-NEGOTIABLE CLINICAL AND SAFETY RULES:
1. RULE 1 (GROUND TRUTH): You MUST use the verified nutrition values provided in the prompt context.
   NEVER invent, hallucinate, alter, or synthesize different calorie, protein, carbohydrate, fat, or micronutrient values.
2. RULE 2 (SAFETY FIRST): You MUST strictly respect all user allergies and dietary preferences (e.g. Vegetarian, Vegan).
   NEVER recommend or suggest any ingredient that conflicts with declared user allergies or dietary boundaries.
3. RULE 3 (NO MEDICAL DIAGNOSIS): You are NOT a doctor. You must NEVER provide medical diagnoses, promise disease cures,
   or prescribe medical treatment. Provide healthy lifestyle, culinary, and dietary guidance only.
4. TONE: Warm, encouraging, concise, culturally sensitive (support Indian and global cuisine naturally), and practical for solo cooks.
"""

ASSISTANT_PROMPT_TEMPLATE = """
User Profile:
- Dietary Preference: {dietary_pref}
- Declared Allergies: {allergies}
- Daily Calorie Target: {target_calories} kcal
- Goal: {goal}
- Meal Slot Context: {meal_slot}

Authoritative Verified Foods from Database Context:
{foods_context}

User Query:
{query}

Respond helpfully, clearly, and concisely. Keep all nutritional references grounded strictly in the verified facts above.
"""

EXPLAIN_PROMPT_TEMPLATE = """
User Context:
- Diet: {dietary_pref}
- Target Calories: {target_calories} kcal
- Goal: {goal}
- Tone: {tone}

Selected Food (Ground Truth from USDA/ICMR database):
- Name: {food_name}
- Calories: {calories} kcal
- Protein: {protein} g
- Carbs: {carbs} g
- Fat: {fat} g
- Category: {category}
- Allergen Flags: {allergens}

Recommendation Score Breakdown:
{score_breakdown_text}

Task:
Explain in 2-3 engaging, warm sentences why this meal is an excellent match for this user.
Provide:
1. A punchy headline.
2. A warm conversational explanation referencing their goal and real nutritional attributes.
3. 2 key health benefits based on the ingredients.
4. A practical 1-sentence preparation/culinary tip.

Output strictly formatted JSON:
{{
  "headline": "...",
  "explanation": "...",
  "key_benefits": ["...", "..."],
  "preparation_tip": "..."
}}
"""

RECIPE_SUGGEST_TEMPLATE = """
User Context:
- Diet: {dietary_pref}
- Allergies: {allergies}
- Target Slot: {meal_slot}
- Target Calories for Slot: ~{target_calories} kcal
- Max Prep Time: {prep_time_limit} mins
- Preferred Cuisine: {cuisine}

Candidate Database Foods Matching Profile:
{candidate_foods_summary}

Task:
Suggest 3 to 4 diverse, delicious, healthy meal recipe ideas specifically designed for {meal_slot} fitting the strict constraints.
Ensure zero allergens are used. Anchor each recipe to a verified candidate food item.

Output strictly formatted JSON:
{{
  "suggestions": [
    {{
      "title": "Recipe Title",
      "meal_slot": "{meal_slot}",
      "estimated_prep_time_mins": 20,
      "matched_catalog_food_id": 123,
      "ingredients": ["100g Paneer", "1 cup Spinach", "1/2 tsp Cumin"],
      "overview": "Brief description...",
      "verified_nutrition_estimate": {{"calories_kcal": 350, "protein_g": 18, "carbohydrates_g": 35, "fat_g": 12}}
    }}
  ]
}}
"""

PANTRY_COOK_TEMPLATE = """
User Context:
- Diet: {dietary_pref}
- Allergies: {allergies}
- Meal Slot: {meal_slot}
- Max Prep Time: {max_prep_time_mins} minutes

Available Pantry Items (In-Stock):
{pantry_items_list}

Authoritative Database Reference Items:
{candidate_foods_summary}

Task:
Suggest 1 or 2 quick recipes that maximize the use of the user's available pantry items.
Zero conflicting allergens allowed.

Output strictly formatted JSON:
{{
  "recipes": [
    {{
      "recipe_name": "...",
      "prep_time_mins": 15,
      "matched_pantry_items": ["..."],
      "missing_items": ["..."],
      "cooking_steps": ["Step 1...", "Step 2..."],
      "nutrition_anchor_food_id": 123,
      "nutrition_anchor_name": "...",
      "nutrition_facts": {{"calories_kcal": 300, "protein_g": 14, "carbs_g": 35, "fat_g": 8}}
    }}
  ]
}}
"""

COMPARE_PROMPT_TEMPLATE = """
User Goal & Priorities:
- Goal: {goal}
- Preference Priority: {preference_priority}

Meal Candidates (Verified Data from Database):
{meals_data_json}

Task:
Compare these meals objectively.
Highlight macronutrient trade-offs, satiety potential, and calorie density.
Identify the recommended winner for the user's specific priority.

Output strictly formatted JSON:
{{
  "analysis": "...",
  "key_tradeoffs": ["Trade-off 1", "Trade-off 2"],
  "winner_for_goal": "Meal Name",
  "macro_comparison": {{
    "highest_protein": "Meal Name",
    "lowest_calorie": "Meal Name",
    "best_budget": "Meal Name"
  }}
}}
"""

COOKING_INSTRUCTION_TEMPLATE = """
Meal to Cook:
- Name: {food_name}
- Servings: {servings}
- User Skill Level: {skill_level}
- Nutrition Profile: {calories} kcal, {protein}g protein, {carbs}g carbs, {fat}g fat
- Dietary Category: {category}

Task:
Provide beginner-friendly, step-by-step cooking instructions.
Include prep time, cook time, equipment needed, exact ingredient list with measurements,
numbered clear steps, and 2 chef tips for great flavor without excess oil/sodium.

Output strictly formatted JSON:
{{
  "prep_time_mins": 10,
  "cook_time_mins": 15,
  "equipment_needed": ["Non-stick pan", "Spatula", "Chef knife"],
  "ingredients": ["..."],
  "step_by_step_instructions": ["1. ...", "2. ..."],
  "chef_tips": ["Tip 1", "Tip 2"]
}}
"""
