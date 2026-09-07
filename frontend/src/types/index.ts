/**
 * DietSense — Shared TypeScript types
 *
 * These interfaces mirror the PostgreSQL schema (backend/db/schema.sql).
 * Keep in sync with any schema changes.
 */

// ─── Users ───────────────────────────────────────────────────────────────────

export type GoalType = "lose_weight" | "maintain_weight" | "gain_weight";
export type ActivityLevel = "sedentary" | "lightly_active" | "moderately_active" | "very_active" | "extra_active";
export type Gender = "male" | "female" | "other" | "prefer_not_to_say";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export interface User {
  id: string;               // UUID (Supabase Auth UID)
  email: string;
  full_name: string;
  age: number;
  gender: Gender;
  height_cm: number;
  weight_kg: number;
  goal: GoalType;
  activity_level: ActivityLevel;
  daily_calorie_target: number;
  created_at: string;
  updated_at: string;
}

export interface DietaryRestriction {
  id: number;
  user_id: string;
  restriction_type: string;  // e.g. "vegetarian", "vegan", "gluten_free"
  allergen_flags: string[];  // e.g. ["nuts", "dairy", "shellfish"]
}

// ─── Foods ───────────────────────────────────────────────────────────────────

export type DataSource = "USDA" | "ICMR_NIN";

export interface Food {
  id: number;
  name: string;
  data_source: DataSource;
  external_id: string;      // USDA fdcId or ICMR-NIN code
  // Macros per 100g
  calories_kcal: number;
  protein_g: number;
  carbohydrates_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
  // Key micronutrients per 100g
  vitamin_a_mcg?: number;
  vitamin_c_mg?: number;
  vitamin_d_mcg?: number;
  calcium_mg?: number;
  iron_mg?: number;
  potassium_mg?: number;
  // Metadata
  allergen_flags: string[];
  food_category: string;
  is_vegetarian: boolean;
  is_vegan: boolean;
  is_gluten_free: boolean;
}

// ─── Recipes ─────────────────────────────────────────────────────────────────

export type CuisineType =
  | "indian" | "mediterranean" | "asian" | "western" | "mexican"
  | "middle_eastern" | "african" | "other";

export interface RecipeIngredient {
  food_id: number;
  food_name: string;
  quantity_grams: number;
}

export type EffortLevel = "low" | "moderate" | "high";
export type MealSlotId = "early_morning" | "breakfast" | "lunch" | "evening_snack" | "dinner";
export type MealFrequency = "2_meals" | "3_meals" | "4_meals" | "5_meals" | "custom";

export interface RecipeIngredientDetail {
  name: string;
  quantity: string;
  grams?: number;
  notes?: string;
}

export interface Recipe {
  id: number;
  name: string;
  description?: string;
  cuisine_type: CuisineType;
  meal_type: MealType;
  effort_level: EffortLevel;
  prep_time_mins: number;
  cook_time_mins: number;
  serving_size_g: number;
  servings: number;
  // Aggregated macros per serving (computed from recipe_ingredients)
  calories_per_serving: number;
  protein_per_serving_g: number;
  carbs_per_serving_g: number;
  fat_per_serving_g: number;
  fiber_per_serving_g: number;
  sodium_per_serving_mg: number;
  // Detailed recipe instructions & solo tips
  prep_steps: string[];
  ingredients_detail: RecipeIngredientDetail[];
  solo_cook_tips?: string[];
  // Flags
  is_vegetarian: boolean;
  is_vegan: boolean;
  is_gluten_free: boolean;
  allergen_flags: string[];
  ingredients: RecipeIngredient[];
}

export interface RecipeData {
  id: number;
  name: string;
  slotId: "early_morning" | "breakfast" | "lunch" | "evening_snack" | "dinner";
  slotLabel: string;
  timeSlot: string;
  icon: string;
  badge: string;
  cuisine: string;
  effortLevel: EffortLevel;
  prepTimeMins: number;
  cookTimeMins: number;
  baseCaloriesPct: number;
  baseProteinPct: number;
  baseCarbsPct: number;
  baseFatPct: number;
  baseFibreG: number;
  tagline: string;
  description: string;
  requiredPantryItems: string[];
  ingredients: { name: string; quantity: string; grams: number; note?: string }[];
  steps: string[];
  soloHacks: string[];
}

export interface PantryItem {
  id: string;
  name: string;
  category: string;
  quantity: string;
  inStock: boolean;
}

// ─── Meal Plans ──────────────────────────────────────────────────────────────

export type PlanStatus = "generated" | "accepted" | "modified" | "completed";

export interface ScoreBreakdown {
  macro_score: number;
  goal_score: number;
  preference_score: number;
  feedback_score: number;
  diversity_score: number;
  prep_score: number;
  total_score: number;
  shap_explanation?: string; // Human-readable SHAP summary
}

export interface MealPlanItem {
  id: number;
  meal_plan_id: number;
  recipe_id: number;
  recipe: Recipe;
  meal_type: MealType;
  serving_multiplier: number;
  score_breakdown: ScoreBreakdown;
}

export interface MealPlan {
  id: number;
  user_id: string;
  date: string;             // ISO date string YYYY-MM-DD
  total_calories_target: number;
  total_calories_actual: number;
  plan_status: PlanStatus;
  items: MealPlanItem[];
  created_at: string;
}

// ─── Feedback ────────────────────────────────────────────────────────────────

export interface UserFeedback {
  id: number;
  meal_plan_item_id: number;
  user_id: string;
  rating: 1 | 2 | 3 | 4 | 5;
  liked_aspects?: string[];
  disliked_aspects?: string[];
  notes?: string;
  created_at: string;
}

// ─── Progress ────────────────────────────────────────────────────────────────

export interface ProgressLog {
  id: number;
  user_id: string;
  date: string;
  weight_kg?: number;
  calories_consumed?: number;
  calories_target: number;
  adherence_score?: number;  // 0–1
  notes?: string;
}

// ─── API Responses ───────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
