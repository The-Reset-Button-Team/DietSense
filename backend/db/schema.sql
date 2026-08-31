-- =============================================================================
-- DietSense — PostgreSQL Database Schema
-- Phase 1: Requirements & Specs
-- =============================================================================
-- Data source rule: ALL calorie/macro values come from USDA FoodData Central
-- or ICMR-NIN (IFCT 2017). The LLM never writes to these tables.
-- =============================================================================

-- Enable UUID extension (needed for user IDs synced with Supabase Auth)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────────────────
-- ENUM TYPES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE goal_type AS ENUM (
    'lose_weight', 'maintain_weight', 'gain_weight'
);

CREATE TYPE activity_level AS ENUM (
    'sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active'
);

CREATE TYPE gender_type AS ENUM (
    'male', 'female', 'other', 'prefer_not_to_say'
);

CREATE TYPE meal_type AS ENUM (
    'breakfast', 'lunch', 'dinner', 'snack'
);

CREATE TYPE cuisine_type AS ENUM (
    'indian', 'mediterranean', 'asian', 'western',
    'mexican', 'middle_eastern', 'african', 'other'
);

CREATE TYPE data_source AS ENUM (
    'USDA', 'ICMR_NIN'
);

CREATE TYPE plan_status AS ENUM (
    'generated', 'accepted', 'modified', 'completed'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: users
-- Synced with Supabase Auth. id = Supabase Auth UUID.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               TEXT NOT NULL UNIQUE,
    full_name           TEXT NOT NULL,
    age                 SMALLINT NOT NULL CHECK (age BETWEEN 2 AND 120),
    gender              gender_type NOT NULL,
    height_cm           NUMERIC(5,2) NOT NULL CHECK (height_cm > 0),
    weight_kg           NUMERIC(5,2) NOT NULL CHECK (weight_kg > 0),
    goal                goal_type NOT NULL DEFAULT 'maintain_weight',
    activity_level      activity_level NOT NULL DEFAULT 'sedentary',
    -- Computed by backend from Harris-Benedict equation + goal adjustment
    daily_calorie_target INTEGER NOT NULL CHECK (daily_calorie_target > 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE users IS
    'User profiles synced with Supabase Auth. id = Supabase Auth UID.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: dietary_restrictions
-- Per-user allergen flags and dietary preferences.
-- Used by the Hard Safety Gate before any scoring.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dietary_restrictions (
    id                  SERIAL PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_vegetarian       BOOLEAN NOT NULL DEFAULT FALSE,
    is_vegan            BOOLEAN NOT NULL DEFAULT FALSE,
    is_gluten_free      BOOLEAN NOT NULL DEFAULT FALSE,
    is_halal            BOOLEAN NOT NULL DEFAULT FALSE,
    is_kosher           BOOLEAN NOT NULL DEFAULT FALSE,
    is_diabetic         BOOLEAN NOT NULL DEFAULT FALSE,
    is_lactose_free     BOOLEAN NOT NULL DEFAULT FALSE,
    allergen_flags      TEXT[] NOT NULL DEFAULT '{}',
    -- e.g. ARRAY['nuts', 'shellfish', 'dairy', 'eggs', 'soy', 'wheat', 'fish']
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id)
);

COMMENT ON TABLE dietary_restrictions IS
    'RULE 2: Hard safety constraints. Queried BEFORE recommendation scoring.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: foods
-- Raw food items from USDA FoodData Central and ICMR-NIN (IFCT 2017).
-- Populated exclusively by ETL scripts (Phase 2). Never by the LLM.
-- All values are PER 100g.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS foods (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    name_local          TEXT,                 -- Regional/vernacular name
    data_source         data_source NOT NULL,
    external_id         TEXT NOT NULL,        -- USDA fdcId or ICMR-NIN code
    food_category       TEXT NOT NULL,        -- e.g. 'legumes', 'dairy', 'cereals'

    -- ─── Macronutrients (per 100g) ─────────────────────────────────────
    calories_kcal       NUMERIC(8,2) NOT NULL CHECK (calories_kcal >= 0),
    protein_g           NUMERIC(7,3) NOT NULL DEFAULT 0 CHECK (protein_g >= 0),
    carbohydrates_g     NUMERIC(7,3) NOT NULL DEFAULT 0 CHECK (carbohydrates_g >= 0),
    fat_g               NUMERIC(7,3) NOT NULL DEFAULT 0 CHECK (fat_g >= 0),
    fiber_g             NUMERIC(7,3) NOT NULL DEFAULT 0 CHECK (fiber_g >= 0),
    sugar_g             NUMERIC(7,3) NOT NULL DEFAULT 0 CHECK (sugar_g >= 0),
    saturated_fat_g     NUMERIC(7,3),
    trans_fat_g         NUMERIC(7,3),
    sodium_mg           NUMERIC(8,2) NOT NULL DEFAULT 0 CHECK (sodium_mg >= 0),

    -- ─── Key Micronutrients (per 100g) ────────────────────────────────
    -- WHO-flagged critical nutrients per healthy diet fact sheet
    vitamin_a_mcg       NUMERIC(8,3),
    vitamin_b12_mcg     NUMERIC(8,3),
    vitamin_c_mg        NUMERIC(8,3),
    vitamin_d_mcg       NUMERIC(8,3),
    folate_mcg          NUMERIC(8,3),
    iron_mg             NUMERIC(8,3),
    calcium_mg          NUMERIC(8,3),
    zinc_mg             NUMERIC(8,3),
    potassium_mg        NUMERIC(8,3),
    iodine_mcg          NUMERIC(8,3),

    -- ─── Safety Flags ─────────────────────────────────────────────────
    allergen_flags      TEXT[] NOT NULL DEFAULT '{}',
    is_vegetarian       BOOLEAN NOT NULL DEFAULT FALSE,
    is_vegan            BOOLEAN NOT NULL DEFAULT FALSE,
    is_gluten_free      BOOLEAN NOT NULL DEFAULT FALSE,
    is_halal            BOOLEAN NOT NULL DEFAULT TRUE,

    -- ─── Metadata ─────────────────────────────────────────────────────
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (data_source, external_id)
);

CREATE INDEX idx_foods_name ON foods USING GIN (to_tsvector('english', name));
CREATE INDEX idx_foods_category ON foods (food_category);
CREATE INDEX idx_foods_source ON foods (data_source);

COMMENT ON TABLE foods IS
    'Authoritative food database. Populated by ETL only. LLM never writes here.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: recipes
-- Composite meals built from foods. Macros are aggregated from recipe_ingredients.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS recipes (
    id                      SERIAL PRIMARY KEY,
    name                    TEXT NOT NULL,
    description             TEXT,
    cuisine_type            cuisine_type NOT NULL DEFAULT 'other',
    meal_type               meal_type NOT NULL,
    prep_time_mins          SMALLINT NOT NULL DEFAULT 0 CHECK (prep_time_mins >= 0),
    cook_time_mins          SMALLINT NOT NULL DEFAULT 0 CHECK (cook_time_mins >= 0),
    serving_size_g          NUMERIC(7,2) NOT NULL CHECK (serving_size_g > 0),
    servings                SMALLINT NOT NULL DEFAULT 1 CHECK (servings > 0),

    -- ─── Aggregated macros per serving (computed, kept denormalized for speed)
    calories_per_serving    NUMERIC(8,2) NOT NULL CHECK (calories_per_serving >= 0),
    protein_per_serving_g   NUMERIC(7,3) NOT NULL DEFAULT 0,
    carbs_per_serving_g     NUMERIC(7,3) NOT NULL DEFAULT 0,
    fat_per_serving_g       NUMERIC(7,3) NOT NULL DEFAULT 0,
    fiber_per_serving_g     NUMERIC(7,3) NOT NULL DEFAULT 0,
    sodium_per_serving_mg   NUMERIC(8,2) NOT NULL DEFAULT 0,

    -- ─── Safety flags (union of all ingredients' flags)
    is_vegetarian           BOOLEAN NOT NULL DEFAULT FALSE,
    is_vegan                BOOLEAN NOT NULL DEFAULT FALSE,
    is_gluten_free          BOOLEAN NOT NULL DEFAULT FALSE,
    allergen_flags          TEXT[] NOT NULL DEFAULT '{}',

    -- ─── Metadata
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recipes_meal_type ON recipes (meal_type);
CREATE INDEX idx_recipes_cuisine ON recipes (cuisine_type);
CREATE INDEX idx_recipes_name ON recipes USING GIN (to_tsvector('english', name));

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: recipe_ingredients
-- Normalized junction: maps recipes to their constituent foods + quantities.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id              SERIAL PRIMARY KEY,
    recipe_id       INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    food_id         INTEGER NOT NULL REFERENCES foods(id) ON DELETE RESTRICT,
    quantity_grams  NUMERIC(8,2) NOT NULL CHECK (quantity_grams > 0),
    notes           TEXT,               -- e.g. "cooked weight", "optional"
    UNIQUE (recipe_id, food_id)
);

CREATE INDEX idx_ri_recipe ON recipe_ingredients (recipe_id);
CREATE INDEX idx_ri_food ON recipe_ingredients (food_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: meal_plans
-- A daily meal plan generated for a user.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS meal_plans (
    id                      SERIAL PRIMARY KEY,
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_date               DATE NOT NULL,
    total_calories_target   INTEGER NOT NULL CHECK (total_calories_target > 0),
    total_calories_actual   INTEGER NOT NULL DEFAULT 0,
    plan_status             plan_status NOT NULL DEFAULT 'generated',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, plan_date)
);

CREATE INDEX idx_meal_plans_user ON meal_plans (user_id);
CREATE INDEX idx_meal_plans_date ON meal_plans (plan_date DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: meal_plan_items
-- Individual meal slots within a plan (breakfast, lunch, dinner, snack).
-- score_breakdown stores the SHAP/scoring detail as JSONB for explainability.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS meal_plan_items (
    id                  SERIAL PRIMARY KEY,
    meal_plan_id        INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id           INTEGER NOT NULL REFERENCES recipes(id) ON DELETE RESTRICT,
    meal_type           meal_type NOT NULL,
    serving_multiplier  NUMERIC(4,2) NOT NULL DEFAULT 1.0 CHECK (serving_multiplier > 0),
    -- JSONB storing: macro_score, goal_score, pref_score, feedback_score,
    --                diversity_score, prep_score, total_score, shap_explanation
    score_breakdown     JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX idx_mpi_plan ON meal_plan_items (meal_plan_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: user_feedback
-- Post-meal ratings that drive the adaptive re-ranking loop.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user_feedback (
    id                  SERIAL PRIMARY KEY,
    meal_plan_item_id   INTEGER NOT NULL REFERENCES meal_plan_items(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating              SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    liked_aspects       TEXT[],         -- e.g. ARRAY['taste', 'portion_size']
    disliked_aspects    TEXT[],         -- e.g. ARRAY['too_spicy', 'prep_time']
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (meal_plan_item_id, user_id)
);

CREATE INDEX idx_feedback_user ON user_feedback (user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: preference_weights
-- Per-user adaptive weight vector, updated after each feedback cycle.
-- Stored as JSONB to allow flexible, evolving preference dimensions.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS preference_weights (
    id                  SERIAL PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- Cuisine preferences: e.g. {"indian": 0.8, "mediterranean": 0.6, "asian": 0.4}
    cuisine_scores      JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Ingredient preferences: e.g. {"chicken": 0.9, "spinach": 0.7}
    ingredient_scores   JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Disliked ingredients: e.g. ["cilantro", "bitter_gourd"]
    disliked_ingredients TEXT[] NOT NULL DEFAULT '{}',
    -- Model metadata
    model_version       TEXT NOT NULL DEFAULT 'v0.1',
    last_trained_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: progress_logs
-- Daily weight and calorie adherence tracking.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS progress_logs (
    id                  SERIAL PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date            DATE NOT NULL,
    weight_kg           NUMERIC(5,2) CHECK (weight_kg > 0),
    calories_consumed   INTEGER CHECK (calories_consumed >= 0),
    calories_target     INTEGER NOT NULL CHECK (calories_target > 0),
    -- adherence_score: 0.0 (0% compliance) to 1.0 (100% compliance)
    adherence_score     NUMERIC(4,3) CHECK (adherence_score BETWEEN 0 AND 1),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, log_date)
);

CREATE INDEX idx_progress_user ON progress_logs (user_id);
CREATE INDEX idx_progress_date ON progress_logs (log_date DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: ai_interaction_logs
-- Audit trail for every Gemini API call.
-- RULE 1 enforcement: shows exactly what context was sent vs. what was received.
-- LLM responses are stored but NEVER written back to foods/recipes/meal_plans.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_interaction_logs (
    id                  SERIAL PRIMARY KEY,
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    interaction_type    TEXT NOT NULL,  -- e.g. 'meal_explanation', 'chat', 'recipe_format'
    -- The structured JSON context sent to Gemini (facts from DB, never hallucinated)
    prompt_context      JSONB NOT NULL,
    -- Raw Gemini response text (natural language only)
    gemini_response     TEXT NOT NULL,
    -- Model used and token usage for cost tracking
    model_name          TEXT NOT NULL DEFAULT 'gemini-1.5-flash',
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    latency_ms          INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_logs_user ON ai_interaction_logs (user_id);
CREATE INDEX idx_ai_logs_type ON ai_interaction_logs (interaction_type);
CREATE INDEX idx_ai_logs_date ON ai_interaction_logs (created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- AUTO-UPDATE TRIGGERS
-- Keep updated_at in sync automatically.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['users','dietary_restrictions','foods','recipes','meal_plans','preference_weights']
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            tbl
        );
    END LOOP;
END;
$$;
