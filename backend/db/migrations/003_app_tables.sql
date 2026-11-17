-- =============================================================================
-- Migration: 003_app_tables.sql
-- Creates application-level tables in Supabase PostgreSQL that mirror the
-- existing SQLite operational tables: profiles, meal_logs, pantry_items.
--
-- These tables extend the core schema (001/002 schema.sql) with the same
-- fields used by the local SQLite database, adapted for PostgreSQL types.
--
-- Idempotent: uses IF NOT EXISTS / IF EXISTS throughout.
-- Non-destructive: never drops existing tables or columns.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: profiles
-- Application-level user preferences and biometrics.
-- Links to public.users via user_id (UUID).
-- Mirrors SQLite profiles table with PostgreSQL-native types.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    full_name       TEXT NOT NULL DEFAULT '',

    -- Dietary preferences
    dietary_pref        TEXT NOT NULL DEFAULT 'vegetarian',
    allergies           JSONB NOT NULL DEFAULT '[]'::JSONB,
    target_calories     INTEGER NOT NULL DEFAULT 2000 CHECK (target_calories > 0),
    budget_per_meal     NUMERIC(8,2) NOT NULL DEFAULT 100.00 CHECK (budget_per_meal > 0),
    prep_time_limit     INTEGER NOT NULL DEFAULT 30 CHECK (prep_time_limit > 0),

    -- Routine settings
    is_solo_cook            BOOLEAN NOT NULL DEFAULT TRUE,
    active_meal_frequency   TEXT NOT NULL DEFAULT '3_meals',

    -- Biometrics
    age             INTEGER NOT NULL DEFAULT 26 CHECK (age BETWEEN 2 AND 120),
    gender          TEXT NOT NULL DEFAULT 'male',
    height_cm       NUMERIC(5,2) NOT NULL DEFAULT 175.0 CHECK (height_cm > 0),
    weight_kg       NUMERIC(5,2) NOT NULL DEFAULT 75.0 CHECK (weight_kg > 0),
    goal            TEXT NOT NULL DEFAULT 'lose_weight',
    activity_level  TEXT NOT NULL DEFAULT 'lightly_active',
    preferred_cuisines JSONB NOT NULL DEFAULT '["indian"]'::JSONB,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast user lookup
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles (user_id);

-- Auto-update trigger for updated_at
DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE public.profiles IS
    'Application-level user preferences and biometrics. Mirrors SQLite profiles table.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: meal_logs
-- Records eaten/skipped meals with skip reasons for adaptive feedback.
-- Links to public.users via user_id (UUID).
-- Mirrors SQLite meal_logs table.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.meal_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    meal_id         TEXT,
    status          TEXT NOT NULL CHECK (status IN ('eaten', 'skipped')),
    reason          TEXT CHECK (reason IS NULL OR reason IN ('time', 'cost', 'taste', 'unavailable')),
    item_tags       JSONB NOT NULL DEFAULT '[]'::JSONB,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Sync metadata: tracks origin for deduplication
    sqlite_id       TEXT UNIQUE,
    synced_at       TIMESTAMPTZ
);

-- Indexes for query patterns used by adaptive feedback loop
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_id ON public.meal_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_time ON public.meal_logs (user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_meal_logs_status ON public.meal_logs (status);

COMMENT ON TABLE public.meal_logs IS
    'Meal eaten/skipped records driving adaptive recommendation reweighting.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: pantry_items
-- User pantry inventory for ingredient-aware meal recommendations.
-- Links to public.users via user_id (UUID).
-- Mirrors SQLite pantry_items table.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.pantry_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL DEFAULT 'General',
    quantity        TEXT NOT NULL DEFAULT '1 unit',
    in_stock        BOOLEAN NOT NULL DEFAULT TRUE,
    source          TEXT NOT NULL DEFAULT 'manual',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Sync metadata
    sqlite_id       TEXT UNIQUE,
    synced_at       TIMESTAMPTZ,

    -- Prevent duplicate items per user
    UNIQUE (user_id, name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pantry_items_user_id ON public.pantry_items (user_id);
CREATE INDEX IF NOT EXISTS idx_pantry_items_in_stock ON public.pantry_items (user_id, in_stock);

-- Auto-update trigger for updated_at
DROP TRIGGER IF EXISTS trg_pantry_items_updated_at ON public.pantry_items;
CREATE TRIGGER trg_pantry_items_updated_at
    BEFORE UPDATE ON public.pantry_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE public.pantry_items IS
    'User pantry inventory. Used for ingredient-aware recommendation scoring.';

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: feedback (app-level, distinct from user_feedback)
-- Lightweight feedback/skip logging used by the adaptive penalty system.
-- Mirrors SQLite feedback table.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.app_feedback (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    meal_id             TEXT,
    status              TEXT NOT NULL,
    reason              TEXT,
    feedback_text       TEXT,
    derived_penalty_tag TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Sync metadata
    sqlite_id           TEXT UNIQUE,
    synced_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_app_feedback_user_id ON public.app_feedback (user_id);

COMMENT ON TABLE public.app_feedback IS
    'App-level feedback/skip records for adaptive penalty system. Mirrors SQLite feedback table.';

-- ─────────────────────────────────────────────────────────────────────────────
-- ROW-LEVEL SECURITY
-- All new tables get RLS policies: users can only access their own rows.
-- ─────────────────────────────────────────────────────────────────────────────

-- profiles RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "profiles_insert_own" ON public.profiles;
CREATE POLICY "profiles_insert_own" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "profiles_delete_own" ON public.profiles;
CREATE POLICY "profiles_delete_own" ON public.profiles
    FOR DELETE USING (auth.uid() = user_id);

-- meal_logs RLS
ALTER TABLE public.meal_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "meal_logs_select_own" ON public.meal_logs;
CREATE POLICY "meal_logs_select_own" ON public.meal_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "meal_logs_insert_own" ON public.meal_logs;
CREATE POLICY "meal_logs_insert_own" ON public.meal_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- pantry_items RLS
ALTER TABLE public.pantry_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "pantry_items_select_own" ON public.pantry_items;
CREATE POLICY "pantry_items_select_own" ON public.pantry_items
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "pantry_items_insert_own" ON public.pantry_items;
CREATE POLICY "pantry_items_insert_own" ON public.pantry_items
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "pantry_items_update_own" ON public.pantry_items;
CREATE POLICY "pantry_items_update_own" ON public.pantry_items
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "pantry_items_delete_own" ON public.pantry_items;
CREATE POLICY "pantry_items_delete_own" ON public.pantry_items
    FOR DELETE USING (auth.uid() = user_id);

-- app_feedback RLS
ALTER TABLE public.app_feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "app_feedback_select_own" ON public.app_feedback;
CREATE POLICY "app_feedback_select_own" ON public.app_feedback
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "app_feedback_insert_own" ON public.app_feedback;
CREATE POLICY "app_feedback_insert_own" ON public.app_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SERVICE ROLE bypass policies
-- Backend uses service role key, which bypasses RLS.
-- These policies ensure the service role can also perform CRUD when needed.
-- (Supabase service_role automatically bypasses RLS, so this is for clarity.)
-- ─────────────────────────────────────────────────────────────────────────────

-- No additional policies needed: service_role key bypasses RLS by default.
