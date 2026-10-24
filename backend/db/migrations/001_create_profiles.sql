-- =============================================================================
-- Migration: 001_create_profiles.sql
-- Native Supabase Auth: public.profiles, RLS Policies, and User Sync Trigger
-- =============================================================================

-- 1. Create public.profiles table referencing Supabase auth.users
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT,
    full_name   TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Enable Row-Level Security on public.profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies on public.profiles
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can delete own profile" ON public.profiles;
CREATE POLICY "Users can delete own profile"
    ON public.profiles
    FOR DELETE
    USING (auth.uid() = id);

-- 4. Trigger Function: Automatically insert profile when a new user signs up in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 5. Enforce Row-Level Security on all user-owned tables
DO $$
BEGIN
    -- users table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users can access own user profile" ON public.users;
        CREATE POLICY "Users can access own user profile" ON public.users
            FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
    END IF;

    -- dietary_restrictions
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'dietary_restrictions') THEN
        ALTER TABLE public.dietary_restrictions ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own dietary restrictions" ON public.dietary_restrictions;
        CREATE POLICY "Users manage own dietary restrictions" ON public.dietary_restrictions
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- meal_plans
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'meal_plans') THEN
        ALTER TABLE public.meal_plans ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own meal plans" ON public.meal_plans;
        CREATE POLICY "Users manage own meal plans" ON public.meal_plans
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- meal_plan_items
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'meal_plan_items') THEN
        ALTER TABLE public.meal_plan_items ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own meal plan items" ON public.meal_plan_items;
        CREATE POLICY "Users manage own meal plan items" ON public.meal_plan_items
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM public.meal_plans
                    WHERE public.meal_plans.id = public.meal_plan_items.meal_plan_id
                      AND public.meal_plans.user_id = auth.uid()
                )
            );
    END IF;

    -- user_feedback
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_feedback') THEN
        ALTER TABLE public.user_feedback ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own feedback" ON public.user_feedback;
        CREATE POLICY "Users manage own feedback" ON public.user_feedback
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- preference_weights
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'preference_weights') THEN
        ALTER TABLE public.preference_weights ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own preference weights" ON public.preference_weights;
        CREATE POLICY "Users manage own preference weights" ON public.preference_weights
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- progress_logs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'progress_logs') THEN
        ALTER TABLE public.progress_logs ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users manage own progress logs" ON public.progress_logs;
        CREATE POLICY "Users manage own progress logs" ON public.progress_logs
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- ai_interaction_logs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ai_interaction_logs') THEN
        ALTER TABLE public.ai_interaction_logs ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Users view own ai interaction logs" ON public.ai_interaction_logs;
        CREATE POLICY "Users view own ai interaction logs" ON public.ai_interaction_logs
            FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;

    -- Public food catalog read-only policies
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'foods') THEN
        ALTER TABLE public.foods ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Public read foods" ON public.foods;
        CREATE POLICY "Public read foods" ON public.foods FOR SELECT USING (true);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'recipes') THEN
        ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Public read recipes" ON public.recipes;
        CREATE POLICY "Public read recipes" ON public.recipes FOR SELECT USING (true);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'recipe_ingredients') THEN
        ALTER TABLE public.recipe_ingredients ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Public read recipe ingredients" ON public.recipe_ingredients;
        CREATE POLICY "Public read recipe ingredients" ON public.recipe_ingredients FOR SELECT USING (true);
    END IF;
END;
$$;
