/**
 * DietSense — TypeScript Types for Gemini AI Features
 * Matches FastAPI schemas defined in backend/app/schemas/ai.py
 */

export interface VerifiedNutrition {
  calories_kcal: number;
  protein_g: number;
  carbohydrates_g: number;
  fat_g: number;
  fiber_g?: number;
  sodium_mg?: number;
}

// ─── 1. AI Meal Assistant ───────────────────────────────────────────────────

export interface AIMealAssistantRequest {
  query: string;
  context_food_ids?: number[];
  meal_slot?: string;
}

export interface AIMealAssistantResponse {
  reply: string;
  suggested_foods: Array<{
    id: number;
    name: string;
    food_category?: string;
    calories_kcal?: number;
    protein_g?: number;
    carbohydrates_g?: number;
    fat_g?: number;
  }>;
  source: string;
  disclaimer: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  suggested_foods?: AIMealAssistantResponse["suggested_foods"];
  source?: string;
  disclaimer?: string;
  timestamp: string;
}

// ─── 2. Meal Recommendation Explanation ─────────────────────────────────────

export interface ExplainRecommendationRequest {
  food_id?: number;
  food_name?: string;
  score_breakdown?: Record<string, number>;
  tone?: string;
}

export interface ExplainRecommendationResponse {
  food_id: number;
  food_name: string;
  headline: string;
  explanation: string;
  key_benefits: string[];
  preparation_tip: string;
  verified_nutrition: VerifiedNutrition;
  source: string;
  disclaimer: string;
}

// ─── 3. Recipe Suggestion ────────────────────────────────────────────────────

export interface RecipeSuggestionRequest {
  meal_slot?: string;
  target_calories?: number;
  prep_time_limit?: number;
  cuisine?: string;
}

export interface RecipeSuggestionItem {
  title: string;
  meal_slot: string;
  estimated_prep_time_mins: number;
  matched_catalog_food_id?: number;
  ingredients: string[];
  overview: string;
  verified_nutrition_estimate: VerifiedNutrition;
}

export interface RecipeSuggestionResponse {
  suggestions: RecipeSuggestionItem[];
  source: string;
  disclaimer: string;
}

// ─── 4. Pantry-Based Cooking Assistant ──────────────────────────────────────

export interface PantryCookingRequest {
  custom_ingredients?: string[];
  max_prep_time_mins?: number;
  meal_slot?: string;
}

export interface PantryRecipeItem {
  recipe_name: string;
  prep_time_mins: number;
  matched_pantry_items: string[];
  missing_items: string[];
  cooking_steps: string[];
  nutrition_anchor_food_id?: number;
  nutrition_anchor_name?: string;
  nutrition_facts: VerifiedNutrition;
}

export interface PantryCookingResponse {
  recipes: PantryRecipeItem[];
  available_pantry_items: string[];
  pantry_matched_count: number;
  source: string;
  disclaimer: string;
}

// ─── 5. Meal Comparison ─────────────────────────────────────────────────────

export interface MealComparisonRequest {
  food_ids: number[];
  preference_priority?: string; // "balanced" | "protein" | "low_calorie" | "budget" | "fiber"
}

export interface MealComparisonResponse {
  compared_meals: Array<{
    id: number;
    name: string;
    food_category?: string;
    calories_kcal?: number;
    protein_g?: number;
    carbohydrates_g?: number;
    fat_g?: number;
    fiber_g?: number;
    sodium_mg?: number;
  }>;
  analysis: string;
  key_tradeoffs: string[];
  winner_for_goal: string;
  macro_comparison: {
    highest_protein?: string;
    lowest_calorie?: string;
    best_budget?: string;
  };
  source: string;
  disclaimer: string;
}

// ─── 6. Cooking Instructions ────────────────────────────────────────────────

export interface CookingInstructionRequest {
  food_id?: number;
  food_name?: string;
  servings?: number;
  skill_level?: string; // "beginner" | "intermediate" | "advanced"
}

export interface CookingInstructionResponse {
  food_id: number;
  food_name: string;
  servings: number;
  prep_time_mins: number;
  cook_time_mins: number;
  equipment_needed: string[];
  ingredients: string[];
  step_by_step_instructions: string[];
  chef_tips: string[];
  verified_nutrition: VerifiedNutrition;
  source: string;
  disclaimer: string;
}
