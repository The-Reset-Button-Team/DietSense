-- =============================================================================
-- Migration: 002_user_profile_meal_logs.sql
-- Completes Profile Attributes, Meal Logs, Meal Plans, and Feedback Tables
-- with Row-Level Security (RLS) as specified in Workflow Brief Section 10
-- =============================================================================

-- 1. Extend public.profiles with onboarding constraints
ALTER TABLE IF EXISTS public.profiles
    ADD COLUMN IF NOT EXISTS dietary_pref TEXT DEFAULT 'vegetarian',
    ADD COLUMN IF NOT EXISTS allergies TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS target_calories INTEGER DEFAULT 2000 CHECK (target_calories > 0),
    ADD COLUMN IF NOT EXISTS budget_per_meal NUMERIC(8,2) DEFAULT 100.00 CHECK (budget_per_meal > 0),
    ADD COLUMN IF NOT EXISTS prep_time_limit INTEGER DEFAULT 30 CHECK (prep_time_limit > 0),
    ADD COLUMN IF NOT EXISTS is_solo_cook BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS active_meal_frequency TEXT DEFAULT '3_meals';

-- 2. Create public.meal_logs table
CREATE TABLE IF NOT EXISTS public.meal_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meal_id     INTEGER,
    status      TEXT NOT NULL CHECK (status IN ('eaten', 'skipped')),
    reason      TEXT CHECK (reason IS NULL OR reason IN ('time', 'cost', 'taste', 'unavailable')),
    item_tags   TEXT[] DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on (user_id, created_at) per Workflow Brief Section 10
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_created ON public.meal_logs (user_id, created_at DESC);

-- Enable RLS on meal_logs
ALTER TABLE public.meal_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own meal logs" ON public.meal_logs;
CREATE POLICY "Users can view own meal logs"
    ON public.meal_logs FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own meal logs" ON public.meal_logs;
CREATE POLICY "Users can insert own meal logs"
    ON public.meal_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 3. Create public.feedback table
CREATE TABLE IF NOT EXISTS public.feedback (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meal_id     INTEGER NOT NULL,
    rating      SMALLINT CHECK (rating BETWEEN 1 AND 5),
    comments    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON public.feedback (user_id);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own feedback" ON public.feedback;
CREATE POLICY "Users can view own feedback"
    ON public.feedback FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own feedback" ON public.feedback;
CREATE POLICY "Users can insert own feedback"
    ON public.feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);
