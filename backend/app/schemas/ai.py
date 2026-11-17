"""
DietSense — Pydantic Schemas for AI & Gemini Integration
Enforces strict input validation and typed JSON responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

STANDARD_MEDICAL_DISCLAIMER = (
    "DietSense provides evidence-based nutritional guidance and does not provide medical "
    "diagnoses, treatment, or disease management. Always consult a healthcare professional "
    "or registered dietitian for clinical needs."
)


# ─── 1. AI Meal Assistant ───────────────────────────────────────────────────

class AIMealAssistantRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="User's natural language meal question")
    context_food_ids: Optional[List[int]] = Field(default=None, description="Optional food IDs from catalog to ground discussion")
    meal_slot: Optional[str] = Field(default=None, description="e.g. breakfast, lunch, dinner, snack")


class AIMealAssistantResponse(BaseModel):
    reply: str
    suggested_foods: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER


# ─── 2. Meal Recommendation Explanation ─────────────────────────────────────

class ExplainRecommendationRequest(BaseModel):
    food_id: Optional[int] = Field(default=None, description="ID of food item from SQLite foods catalog")
    food_name: Optional[str] = Field(default=None, description="Optional override name of the dish")
    score_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="ML scoring breakdown components")
    tone: str = Field(default="friendly", description="friendly, clinical, or hinglish")


class ExplainRecommendationResponse(BaseModel):
    food_id: int
    food_name: str
    headline: str
    explanation: str
    key_benefits: List[str] = Field(default_factory=list)
    preparation_tip: str
    verified_nutrition: Dict[str, Any]
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER


# ─── 3. Recipe Suggestion ────────────────────────────────────────────────────

class RecipeSuggestionRequest(BaseModel):
    meal_slot: Optional[str] = Field(default="lunch", description="early_morning, breakfast, lunch, evening_snack, dinner")
    target_calories: Optional[int] = Field(default=None, ge=100, le=2500)
    prep_time_limit: Optional[int] = Field(default=30, ge=5, le=180)
    cuisine: Optional[str] = Field(default="indian")


class RecipeSuggestionItem(BaseModel):
    title: str
    meal_slot: str
    estimated_prep_time_mins: int
    matched_catalog_food_id: Optional[int] = None
    ingredients: List[str]
    overview: str
    verified_nutrition_estimate: Dict[str, Any]


class RecipeSuggestionResponse(BaseModel):
    suggestions: List[RecipeSuggestionItem]
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER


# ─── 4. Pantry-Based Cooking Assistant ──────────────────────────────────────

class PantryCookingRequest(BaseModel):
    custom_ingredients: Optional[List[str]] = Field(default=None, description="Optional extra ingredients to include")
    max_prep_time_mins: Optional[int] = Field(default=25, ge=5, le=120)
    meal_slot: Optional[str] = Field(default="dinner")


class PantryRecipeItem(BaseModel):
    recipe_name: str
    prep_time_mins: int
    matched_pantry_items: List[str]
    missing_items: List[str] = Field(default_factory=list)
    cooking_steps: List[str]
    nutrition_anchor_food_id: Optional[int] = None
    nutrition_anchor_name: Optional[str] = None
    nutrition_facts: Dict[str, Any]


class PantryCookingResponse(BaseModel):
    recipes: List[PantryRecipeItem]
    available_pantry_items: List[str]
    pantry_matched_count: int
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER


# ─── 5. Meal Comparison ─────────────────────────────────────────────────────

class MealComparisonRequest(BaseModel):
    food_ids: List[int] = Field(..., min_length=2, max_length=5, description="2 to 5 food catalog IDs to compare")
    preference_priority: Optional[str] = Field(default="balanced", description="balanced, protein, low_calorie, budget, fiber")


class MealComparisonResponse(BaseModel):
    compared_meals: List[Dict[str, Any]]
    analysis: str
    key_tradeoffs: List[str] = Field(default_factory=list)
    winner_for_goal: str
    macro_comparison: Dict[str, Any]
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER


# ─── 6. Cooking Instructions ────────────────────────────────────────────────

class CookingInstructionRequest(BaseModel):
    food_id: Optional[int] = Field(default=None, description="Food catalog ID from foods table")
    food_name: Optional[str] = Field(default=None, description="Optional override name of the dish")
    servings: int = Field(default=1, ge=1, le=10)
    skill_level: str = Field(default="beginner", description="beginner, intermediate, advanced")


class CookingInstructionResponse(BaseModel):
    food_id: int
    food_name: str
    servings: int
    prep_time_mins: int
    cook_time_mins: int
    equipment_needed: List[str]
    ingredients: List[str]
    step_by_step_instructions: List[str]
    chef_tips: List[str]
    verified_nutrition: Dict[str, Any]
    source: str = "gemini-3.8-flash"
    disclaimer: str = STANDARD_MEDICAL_DISCLAIMER
