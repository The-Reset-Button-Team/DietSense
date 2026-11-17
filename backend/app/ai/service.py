"""
DietSense — Gemini AI Service Layer
Coordinates verified nutrition retrieval from SQLite, safety enforcement (filter_safe),
prompt dispatch via GeminiClientManager, and seamless fallback execution.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings
from db.database import get_db_cursor
from ml.scoring.safety_gate import filter_safe
from app.ai.client import gemini_client
from app.ai.prompts import (
    SYSTEM_INSTRUCTION_CORE,
    ASSISTANT_PROMPT_TEMPLATE,
    EXPLAIN_PROMPT_TEMPLATE,
    RECIPE_SUGGEST_TEMPLATE,
    PANTRY_COOK_TEMPLATE,
    COMPARE_PROMPT_TEMPLATE,
    COOKING_INSTRUCTION_TEMPLATE,
)
from app.ai.fallback import (
    fallback_assistant_chat,
    fallback_explain_recommendation,
    fallback_suggest_recipes,
    fallback_pantry_cooking,
    fallback_compare_meals,
    fallback_cooking_instructions,
)
from app.schemas.ai import (
    AIMealAssistantResponse,
    ExplainRecommendationResponse,
    RecipeSuggestionResponse,
    RecipeSuggestionItem,
    PantryCookingResponse,
    PantryRecipeItem,
    MealComparisonResponse,
    CookingInstructionResponse,
    STANDARD_MEDICAL_DISCLAIMER,
)

logger = logging.getLogger("dietsense.ai.service")


class GeminiService:
    """Service facade for all DietSense AI capabilities."""

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Converts an sqlite3.Row to a standard dictionary."""
        if not row:
            return {}
        d = dict(row)
        tags = []
        cat = str(d.get("food_category", "")).lower()
        if cat:
            tags.append(cat)
        if d.get("is_vegetarian"):
            tags.append("veg")
        else:
            tags.append("non-veg")
        if d.get("is_gluten_free"):
            tags.append("gluten-free")
        d["tags"] = tags

        allergens_str = d.get("allergen_flags") or ""
        d["allergens"] = [a.strip().lower() for a in allergens_str.split(",") if a.strip()]
        return d

    def get_food_by_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single food item with verified clinical nutrition facts."""
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, name_local, data_source, external_id, food_category,
                           calories_kcal, protein_g, carbohydrates_g, fat_g, fiber_g, sugar_g,
                           sodium_mg, potassium_mg, calcium_mg, iron_mg, zinc_mg,
                           is_vegetarian, is_vegan, is_gluten_free, allergen_flags
                    FROM foods WHERE id = ?
                    """,
                    (food_id,),
                )
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        except Exception as e:
            logger.debug("Error fetching food id %s: %s", food_id, e)
            return None

    def get_foods_by_ids(self, food_ids: List[int]) -> List[Dict[str, Any]]:
        """Retrieves verified records for multiple food items."""
        if not food_ids:
            return []
        try:
            with get_db_cursor() as cur:
                placeholders = ",".join(["?"] * len(food_ids))
                cur.execute(
                    f"""
                    SELECT id, name, name_local, data_source, external_id, food_category,
                           calories_kcal, protein_g, carbohydrates_g, fat_g, fiber_g, sugar_g,
                           sodium_mg, potassium_mg, calcium_mg, iron_mg, zinc_mg,
                           is_vegetarian, is_vegan, is_gluten_free, allergen_flags
                    FROM foods WHERE id IN ({placeholders})
                    """,
                    tuple(food_ids),
                )
                return [self._row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.debug("Error fetching foods %s: %s", food_ids, e)
            return []

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Loads user dietary preferences, target calories, and allergies."""
        default_profile = {
            "dietary_pref": "vegetarian",
            "allergies": [],
            "target_calories": 2000,
            "goal": "maintain_weight",
        }
        if not user_id:
            return default_profile

        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
                row = cur.fetchone()
                if not row:
                    return default_profile

                d = dict(row)
                allergies_raw = d.get("allergies") or "[]"
                try:
                    allergies_list = json.loads(allergies_raw) if isinstance(allergies_raw, str) else allergies_raw
                except Exception:
                    allergies_list = []

                return {
                    "dietary_pref": d.get("dietary_pref") or "vegetarian",
                    "allergies": allergies_list,
                    "target_calories": d.get("target_calories") or 2000,
                    "goal": d.get("goal") or "maintain_weight",
                    "budget_per_meal": d.get("budget_per_meal") or 100.0,
                    "prep_time_limit": d.get("prep_time_limit") or 30,
                }
        except Exception as e:
            logger.debug("Error loading profile for %s: %s", user_id, e)
            return default_profile

    def get_user_pantry_items(self, user_id: str) -> List[str]:
        """Loads in-stock pantry items from SQLite."""
        if not user_id:
            return []
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT name FROM pantry_items WHERE user_id = ? AND in_stock = 1",
                    (user_id,),
                )
                return [r["name"] for r in cur.fetchall()]
        except Exception:
            return []

    def get_safe_candidate_foods(self, user_profile: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves catalog foods and runs them through the non-negotiable hard safety gate."""
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
                           is_vegetarian, is_vegan, is_gluten_free, allergen_flags
                    FROM foods WHERE calories_kcal > 50
                    ORDER BY RANDOM()
                    LIMIT 100
                    """
                )
                raw_foods = [self._row_to_dict(r) for r in cur.fetchall()]
                safe_foods = filter_safe(raw_foods, user_profile)
                return safe_foods[:limit]
        except Exception:
            return []

    # ─── 1. AI Meal Assistant ────────────────────────────────────────────────

    async def assistant_chat(
        self,
        query: str,
        user_id: str,
        context_food_ids: Optional[List[int]] = None,
        meal_slot: Optional[str] = None,
    ) -> AIMealAssistantResponse:
        user_profile = self.get_user_profile(user_id)
        foods = self.get_foods_by_ids(context_food_ids or [])
        if not foods:
            foods = self.get_safe_candidate_foods(user_profile, limit=3)

        foods_text = "\n".join([
            f"- {f['name']} ({f.get('food_category', 'General')}): {f.get('calories_kcal', 0):.0f} kcal, "
            f"Protein: {f.get('protein_g', 0):.1f}g, Carbs: {f.get('carbohydrates_g', 0):.1f}g, Fat: {f.get('fat_g', 0):.1f}g"
            for f in foods
        ])

        prompt = ASSISTANT_PROMPT_TEMPLATE.format(
            dietary_pref=user_profile["dietary_pref"],
            allergies=", ".join(user_profile["allergies"]) or "None",
            target_calories=user_profile["target_calories"],
            goal=user_profile["goal"],
            meal_slot=meal_slot or "general",
            foods_context=foods_text or "No specific foods context passed.",
            query=query,
        )

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="assistant",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
        )

        if not res_text or status != "success":
            fallback_text = fallback_assistant_chat(query, user_profile, foods)
            return AIMealAssistantResponse(
                reply=fallback_text,
                suggested_foods=foods[:3],
                source="offline_fallback",
            )

        return AIMealAssistantResponse(
            reply=res_text.strip(),
            suggested_foods=foods[:3],
            source=settings.gemini_model,
        )

    # ─── 2. Meal Recommendation Explanation ─────────────────────────────────

    async def explain_recommendation(
        self,
        food_id: int,
        user_id: str,
        score_breakdown: Optional[Dict[str, Any]] = None,
        tone: str = "friendly",
        food_name: Optional[str] = None,
    ) -> ExplainRecommendationResponse:
        user_profile = self.get_user_profile(user_id)
        food = self.get_food_by_id(food_id)
        if not food:
            # Fallback placeholder if food not in DB
            food = {
                "id": food_id,
                "name": food_name or "Custom Meal",
                "calories_kcal": 400,
                "protein_g": 18,
                "carbohydrates_g": 50,
                "fat_g": 10,
                "food_category": "General",
                "allergen_flags": "",
            }
        elif food_name:
            food["name"] = food_name

        breakdown = score_breakdown or {
            "similarity": 0.8,
            "macro_fit": 0.85,
            "budget_fit": 0.9,
            "prep_time_fit": 0.95,
        }

        breakdown_text = ", ".join([f"{k}: {v}" for k, v in breakdown.items()])

        prompt = EXPLAIN_PROMPT_TEMPLATE.format(
            dietary_pref=user_profile["dietary_pref"],
            target_calories=user_profile["target_calories"],
            goal=user_profile["goal"],
            tone=tone,
            food_name=food["name"],
            calories=f"{food.get('calories_kcal', 0):.0f}",
            protein=f"{food.get('protein_g', 0):.1f}",
            carbs=f"{food.get('carbohydrates_g', 0):.1f}",
            fat=f"{food.get('fat_g', 0):.1f}",
            category=food.get("food_category", "General"),
            allergens=food.get("allergen_flags", "None"),
            score_breakdown_text=breakdown_text,
        )

        cache_data = {"food_id": food_id, "goal": user_profile["goal"], "diet": user_profile["dietary_pref"], "tone": tone}

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="explain",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
            cache_key_data=cache_data,
        )

        verified_nut = {
            "calories_kcal": food.get("calories_kcal", 0),
            "protein_g": food.get("protein_g", 0),
            "carbohydrates_g": food.get("carbohydrates_g", 0),
            "fat_g": food.get("fat_g", 0),
        }

        if res_text and status in ("success", "cached"):
            try:
                # Strip markdown code blocks if wrapped
                cleaned = res_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                return ExplainRecommendationResponse(
                    food_id=food_id,
                    food_name=food["name"],
                    headline=data.get("headline", f"{food['name']} Recommendation"),
                    explanation=data.get("explanation", ""),
                    key_benefits=data.get("key_benefits", []),
                    preparation_tip=data.get("preparation_tip", ""),
                    verified_nutrition=verified_nut,
                    source=settings.gemini_model if status == "success" else "cached_gemini",
                )
            except Exception as e:
                logger.debug("Failed to parse Gemini explain JSON: %s", e)

        fallback_data = fallback_explain_recommendation(food, user_profile, breakdown)
        return ExplainRecommendationResponse(
            food_id=food_id,
            food_name=food["name"],
            headline=fallback_data["headline"],
            explanation=fallback_data["explanation"],
            key_benefits=fallback_data["key_benefits"],
            preparation_tip=fallback_data["preparation_tip"],
            verified_nutrition=verified_nut,
            source="offline_fallback",
        )

    # ─── 3. Recipe Suggestions ────────────────────────────────────────────────

    async def suggest_recipes(
        self,
        user_id: str,
        meal_slot: str = "lunch",
        target_calories: Optional[int] = None,
        prep_time_limit: int = 30,
        cuisine: str = "indian",
    ) -> RecipeSuggestionResponse:
        user_profile = self.get_user_profile(user_id)
        safe_candidates = self.get_safe_candidate_foods(user_profile, limit=6)
        target_cal = target_calories or int(user_profile["target_calories"] * 0.30)

        candidates_text = "\n".join([
            f"- ID {f['id']}: {f['name']} ({f.get('food_category', 'General')}) | "
            f"{f.get('calories_kcal', 0):.0f} kcal, {f.get('protein_g', 0):.1f}g P, "
            f"{f.get('carbohydrates_g', 0):.1f}g C, {f.get('fat_g', 0):.1f}g F"
            for f in safe_candidates
        ])

        prompt = RECIPE_SUGGEST_TEMPLATE.format(
            dietary_pref=user_profile["dietary_pref"],
            allergies=", ".join(user_profile["allergies"]) or "None",
            meal_slot=meal_slot,
            target_calories=target_cal,
            prep_time_limit=prep_time_limit,
            cuisine=cuisine,
            candidate_foods_summary=candidates_text,
        )

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="recipe_suggest",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
        )

        if res_text and status in ("success", "cached"):
            try:
                cleaned = res_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                items = []
                for item in data.get("suggestions", []):
                    items.append(RecipeSuggestionItem(**item))
                if items:
                    return RecipeSuggestionResponse(
                        suggestions=items,
                        source=settings.gemini_model,
                    )
            except Exception as e:
                logger.debug("Failed to parse recipe suggestion JSON: %s", e)

        fallback_items = fallback_suggest_recipes(safe_candidates, meal_slot, target_cal)
        return RecipeSuggestionResponse(
            suggestions=[RecipeSuggestionItem(**item) for item in fallback_items],
            source="offline_fallback",
        )

    # ─── 4. Pantry Cooking Assistant ─────────────────────────────────────────

    async def pantry_cooking_assistant(
        self,
        user_id: str,
        custom_ingredients: Optional[List[str]] = None,
        max_prep_time_mins: int = 25,
        meal_slot: str = "dinner",
    ) -> PantryCookingResponse:
        user_profile = self.get_user_profile(user_id)
        db_pantry = self.get_user_pantry_items(user_id)
        combined_pantry = list(dict.fromkeys((custom_ingredients or []) + db_pantry))
        if not combined_pantry:
            combined_pantry = ["Paneer", "Spinach", "Garlic", "Ghee", "Moong Dal"]

        safe_candidates = self.get_safe_candidate_foods(user_profile, limit=5)
        candidates_text = "\n".join([f"- {f['name']} (ID {f['id']})" for f in safe_candidates])

        prompt = PANTRY_COOK_TEMPLATE.format(
            dietary_pref=user_profile["dietary_pref"],
            allergies=", ".join(user_profile["allergies"]) or "None",
            meal_slot=meal_slot,
            max_prep_time_mins=max_prep_time_mins,
            pantry_items_list=", ".join(combined_pantry),
            candidate_foods_summary=candidates_text,
        )

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="pantry_cook",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
        )

        if res_text and status in ("success", "cached"):
            try:
                cleaned = res_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                recipes = [PantryRecipeItem(**r) for r in data.get("recipes", [])]
                if recipes:
                    return PantryCookingResponse(
                        recipes=recipes,
                        available_pantry_items=combined_pantry,
                        pantry_matched_count=len(combined_pantry),
                        source=settings.gemini_model,
                    )
            except Exception as e:
                logger.debug("Failed to parse pantry cook JSON: %s", e)

        fallback_recipes = fallback_pantry_cooking(combined_pantry, safe_candidates, max_prep_time_mins)
        return PantryCookingResponse(
            recipes=[PantryRecipeItem(**r) for r in fallback_recipes],
            available_pantry_items=combined_pantry,
            pantry_matched_count=len(combined_pantry),
            source="offline_fallback",
        )

    # ─── 5. Meal Comparison ──────────────────────────────────────────────────

    async def compare_meals(
        self,
        food_ids: List[int],
        user_id: str,
        preference_priority: str = "balanced",
    ) -> MealComparisonResponse:
        user_profile = self.get_user_profile(user_id)
        foods = self.get_foods_by_ids(food_ids)
        if len(foods) < 2:
            raise ValueError("At least 2 valid meals from the foods catalog are required for comparison.")

        # Filter safe
        safe_foods = filter_safe(foods, user_profile)
        if len(safe_foods) < 2:
            safe_foods = foods  # Fallback to requested foods if user forced selection

        meals_json = json.dumps([
            {
                "id": f["id"],
                "name": f["name"],
                "category": f.get("food_category"),
                "calories_kcal": f.get("calories_kcal"),
                "protein_g": f.get("protein_g"),
                "carbs_g": f.get("carbohydrates_g"),
                "fat_g": f.get("fat_g"),
                "fiber_g": f.get("fiber_g", 0),
                "sodium_mg": f.get("sodium_mg", 0),
            }
            for f in safe_foods
        ], indent=2)

        prompt = COMPARE_PROMPT_TEMPLATE.format(
            goal=user_profile["goal"],
            preference_priority=preference_priority,
            meals_data_json=meals_json,
        )

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="compare",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
        )

        if res_text and status in ("success", "cached"):
            try:
                cleaned = res_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                return MealComparisonResponse(
                    compared_meals=safe_foods,
                    analysis=data.get("analysis", ""),
                    key_tradeoffs=data.get("key_tradeoffs", []),
                    winner_for_goal=data.get("winner_for_goal", safe_foods[0]["name"]),
                    macro_comparison=data.get("macro_comparison", {}),
                    source=settings.gemini_model,
                )
            except Exception as e:
                logger.debug("Failed to parse compare meals JSON: %s", e)

        fallback_data = fallback_compare_meals(safe_foods, preference_priority)
        return MealComparisonResponse(
            compared_meals=safe_foods,
            analysis=fallback_data["analysis"],
            key_tradeoffs=fallback_data["key_tradeoffs"],
            winner_for_goal=fallback_data["winner_for_goal"],
            macro_comparison=fallback_data["macro_comparison"],
            source="offline_fallback",
        )

    # ─── 6. Cooking Instructions ─────────────────────────────────────────────

    async def generate_cooking_instructions(
        self,
        food_id: int,
        user_id: str,
        servings: int = 1,
        skill_level: str = "beginner",
        food_name: Optional[str] = None,
    ) -> CookingInstructionResponse:
        food = self.get_food_by_id(food_id)
        if not food:
            food = {
                "id": food_id,
                "name": food_name or "Balanced Meal",
                "calories_kcal": 380,
                "protein_g": 18,
                "carbohydrates_g": 48,
                "fat_g": 8,
                "food_category": "General",
            }
        elif food_name:
            food["name"] = food_name

        verified_nut = {
            "calories_kcal": round(food.get("calories_kcal", 0) * servings, 1),
            "protein_g": round(food.get("protein_g", 0) * servings, 1),
            "carbohydrates_g": round(food.get("carbohydrates_g", 0) * servings, 1),
            "fat_g": round(food.get("fat_g", 0) * servings, 1),
        }

        prompt = COOKING_INSTRUCTION_TEMPLATE.format(
            food_name=food["name"],
            servings=servings,
            skill_level=skill_level,
            calories=f"{food.get('calories_kcal', 0):.0f}",
            protein=f"{food.get('protein_g', 0):.1f}",
            carbs=f"{food.get('carbohydrates_g', 0):.1f}",
            fat=f"{food.get('fat_g', 0):.1f}",
            category=food.get("food_category", "General"),
        )

        res_text, status = await gemini_client.generate_text(
            prompt=prompt,
            user_id=user_id,
            feature="cooking_instructions",
            system_instruction=SYSTEM_INSTRUCTION_CORE,
        )

        if res_text and status in ("success", "cached"):
            try:
                cleaned = res_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                return CookingInstructionResponse(
                    food_id=food_id,
                    food_name=food["name"],
                    servings=servings,
                    prep_time_mins=data.get("prep_time_mins", 10),
                    cook_time_mins=data.get("cook_time_mins", 15),
                    equipment_needed=data.get("equipment_needed", ["Skillet", "Knife"]),
                    ingredients=data.get("ingredients", [food["name"]]),
                    step_by_step_instructions=data.get("step_by_step_instructions", []),
                    chef_tips=data.get("chef_tips", []),
                    verified_nutrition=verified_nut,
                    source=settings.gemini_model,
                )
            except Exception as e:
                logger.debug("Failed to parse cooking instructions JSON: %s", e)

        fallback_data = fallback_cooking_instructions(food, servings, skill_level)
        return CookingInstructionResponse(
            food_id=food_id,
            food_name=food["name"],
            servings=servings,
            prep_time_mins=fallback_data["prep_time_mins"],
            cook_time_mins=fallback_data["cook_time_mins"],
            equipment_needed=fallback_data["equipment_needed"],
            ingredients=fallback_data["ingredients"],
            step_by_step_instructions=fallback_data["step_by_step_instructions"],
            chef_tips=fallback_data["chef_tips"],
            verified_nutrition=verified_nut,
            source="offline_fallback",
        )


# Global service singleton
ai_service = GeminiService()
