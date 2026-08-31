-- =============================================================================
-- DietSense — Seed Data
-- Phase 1: Reference / lookup data.
-- Run AFTER schema.sql.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- NOTE: foods and recipes are NOT seeded here.
-- They are populated by the ETL pipeline in Phase 2 (scripts/).
-- ─────────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────────
-- Sample / Test User (development only — DO NOT use in production)
-- Password: change-this-in-supabase-auth
-- ─────────────────────────────────────────────────────────────────────────────

-- INSERT INTO users (id, email, full_name, age, gender, height_cm, weight_kg,
--                    goal, activity_level, daily_calorie_target)
-- VALUES (
--     '00000000-0000-0000-0000-000000000001',  -- placeholder UUID
--     'dev@dietsense.local',
--     'Dev User',
--     25, 'male', 175.0, 75.0,
--     'lose_weight', 'moderately_active', 1800
-- ) ON CONFLICT (email) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- Default preference_weights row inserted when a user registers
-- (handled by backend trigger / registration endpoint in Phase 4)
-- ─────────────────────────────────────────────────────────────────────────────
-- Example default:
-- INSERT INTO preference_weights (user_id, cuisine_scores, ingredient_scores)
-- VALUES ('<user_uuid>', '{}', '{}') ON CONFLICT (user_id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- WHO Dietary Reference Values (stored as app config, not user data)
-- These anchor the macro_match_score and goal_alignment_score in the ML engine.
-- Source: WHO Healthy Diet Fact Sheet (2026-01-26)
-- ─────────────────────────────────────────────────────────────────────────────

-- These values are hard-coded as constants in ml/scoring/formula.py (Phase 6).
-- Reference only:
--
--  Carbohydrates:  45–75% total energy
--  Free Sugars:    < 10% total energy (optimal < 5%)
--  Total Fat:      15–30% total energy
--  Saturated Fat:  < 10% total energy
--  Trans Fat:      < 1%  total energy
--  Protein:        10–15% total energy
--  Salt:           < 5 g/day (adults)
--  Sodium:         < 2 g/day (adults)
--  Potassium:      ≥ 3510 mg/day (adults)
--  Fruit & Veg:    ≥ 400 g/day (age > 10)
--  Dietary Fibre:  ≥ 25 g/day (age > 10)
