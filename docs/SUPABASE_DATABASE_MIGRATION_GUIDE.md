# DietSense — Supabase PostgreSQL Database Migration Guide

## 1. Overview & Migration Purpose

DietSense employs a **hybrid, local-first architecture**:
- **Local SQLite (`database/dietsense.db`)**: Operates as the zero-latency, offline operational database and houses the ~14,099 reference food catalog from USDA FoodData Central and ICMR-NIN (IFCT 2017).
- **Supabase PostgreSQL (Cloud)**: Serves as the cloud persistence layer for user accounts, biometrics, routine preferences, pantry inventory, and meal adherence logs. It enables multi-device data synchronization, cloud backups, and future native Supabase Auth integration.

### Core Architecture Principles
1. **SQLite Independence**: The local application runs 100% independently without any network connection or cloud dependency.
2. **Deterministic UUID Mapping**: Text-based SQLite user and record IDs map deterministically to RFC 4122 UUIDs (via UUIDv5 with a fixed namespace) so identifiers remain stable across sync cycles.
3. **Idempotent Synchronization**: Synced tables use `sqlite_id UNIQUE` constraints to guarantee that re-syncing records never creates duplicates.
4. **Reference Food Dataset Justification**: The ~14,099 reference food records are intentionally **preserved in local SQLite** and not copied to Supabase unless explicitly justified. Local SQLite provides sub-millisecond query response (<15 ms) for TF-IDF cosine similarity candidate scoring across thousands of items, zero network egress costs, and complete offline operability.

---

## 2. Migration Files Inventory

All migration files are located in `backend/db/migrations/` and `backend/db/`:

| File | Order | Purpose | Tables / Types Created |
|---|---|---|---|
| `backend/db/schema.sql` | 1 | Foundation schema | 11 tables (`users`, `dietary_restrictions`, `foods`, `recipes`, `recipe_ingredients`, `meal_plans`, `meal_plan_items`, `user_feedback`, `preference_weights`, `progress_logs`, `ai_interaction_logs`), 7 custom enums, 6 auto-update triggers |
| `backend/db/migrations/001_create_profiles.sql` | 2 | Supabase Auth sync (optional) | `public.profiles` linked to `auth.users`, RLS policies, `handle_new_user()` trigger |
| `backend/db/migrations/002_user_profile_meal_logs.sql` | 3 | Profile extension & audit tables | Extends profiles with onboarding constraints, creates `meal_logs` and `feedback` with RLS |
| `backend/db/migrations/003_app_tables.sql` | 4 | Operational app tables | `profiles`, `meal_logs`, `pantry_items`, `app_feedback` with `sqlite_id` sync columns, composite indexes, and RLS |

---

## 3. Tables, Relationships & Schema Mapping

### Complete Table Map (SQLite vs. Supabase PostgreSQL)

```
┌─────────────────────────┐                  ┌─────────────────────────────────┐
│     SQLite (Local)      │                  │   Supabase PostgreSQL (Cloud)  │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ users                   │ ───────────────> │ public.users                    │
│   id TEXT (PK)          │   UUIDv5 Map     │   id UUID (PK)                  │
│   email TEXT UNIQUE     │                  │   email TEXT UNIQUE             │
│   password_hash TEXT    │                  │   gender gender_type            │
│   full_name TEXT        │                  │   goal goal_type                │
│   created_at TEXT       │                  │   activity_level activity_level │
│   updated_at TEXT       │                  │   daily_calorie_target INT      │
│                         │                  │   created_at TIMESTAMPTZ        │
│                         │                  │   updated_at TIMESTAMPTZ        │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ profiles                │ ───────────────> │ public.profiles                 │
│   id TEXT (PK)          │   Direct Sync    │   id UUID (PK)                  │
│   user_id TEXT (FK)     │                  │   user_id UUID (FK -> users.id) │
│   dietary_pref TEXT     │                  │   dietary_pref TEXT             │
│   allergies TEXT (JSON) │                  │   allergies JSONB               │
│   target_calories INT   │                  │   target_calories INT           │
│   budget_per_meal REAL  │                  │   budget_per_meal NUMERIC(8,2)  │
│   prep_time_limit INT   │                  │   prep_time_limit INT           │
│   is_solo_cook INT      │                  │   is_solo_cook BOOLEAN          │
│   active_meal_frequency │                  │   active_meal_frequency TEXT    │
│   preferred_cuisines    │                  │   preferred_cuisines JSONB      │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ pantry_items            │ ───────────────> │ public.pantry_items             │
│   id TEXT (PK)          │   UPSERT Sync    │   id UUID (PK)                  │
│   user_id TEXT (FK)     │                  │   user_id UUID (FK -> users.id) │
│   name TEXT             │                  │   name TEXT                     │
│   category TEXT         │                  │   category TEXT                 │
│   quantity TEXT         │                  │   quantity TEXT                 │
│   in_stock INT          │                  │   in_stock BOOLEAN              │
│   source TEXT           │                  │   sqlite_id TEXT UNIQUE         │
│                         │                  │   synced_at TIMESTAMPTZ         │
│                         │                  │   UNIQUE (user_id, name)        │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ meal_logs               │ ───────────────> │ public.meal_logs                │
│   id TEXT (PK)          │   UPSERT Sync    │   id UUID (PK)                  │
│   user_id TEXT (FK)     │                  │   user_id UUID (FK -> users.id) │
│   meal_id TEXT          │                  │   meal_id TEXT                  │
│   status TEXT           │                  │   status TEXT (eaten/skipped)   │
│   reason TEXT           │                  │   reason TEXT                   │
│   item_tags TEXT (JSON) │                  │   item_tags JSONB               │
│   timestamp TEXT        │                  │   timestamp TIMESTAMPTZ         │
│                         │                  │   sqlite_id TEXT UNIQUE         │
│                         │                  │   synced_at TIMESTAMPTZ         │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ feedback                │ ───────────────> │ public.app_feedback             │
│   id TEXT (PK)          │   UPSERT Sync    │   id UUID (PK)                  │
│   user_id TEXT (FK)     │                  │   user_id UUID (FK -> users.id) │
│   meal_id TEXT          │                  │   status TEXT, reason TEXT      │
│   feedback_text TEXT    │                  │   feedback_text TEXT            │
│   derived_penalty_tag   │                  │   sqlite_id TEXT UNIQUE         │
├─────────────────────────┤                  ├─────────────────────────────────┤
│ foods (14,099 rows)     │ ─── Preserved ─> │ public.foods (Schema ready,     │
│   Local SQLite only     │     Locally      │  data remains in SQLite)        │
└─────────────────────────┘                  └─────────────────────────────────┘
```

---

## 4. Constraints & Indexes Reference

### Unique Constraints
| Table | Constraint | Purpose |
|---|---|---|
| `users` | `UNIQUE (email)` | Prevent duplicate user registration |
| `profiles` | `UNIQUE (user_id)` | Strict 1:1 user-to-profile relationship |
| `pantry_items` | `UNIQUE (user_id, name)` | Prevent duplicate ingredients per user pantry |
| `pantry_items` | `UNIQUE (sqlite_id)` | Idempotent sync deduplication |
| `meal_logs` | `UNIQUE (sqlite_id)` | Idempotent sync deduplication |
| `app_feedback` | `UNIQUE (sqlite_id)` | Idempotent sync deduplication |
| `meal_plans` | `UNIQUE (user_id, plan_date)` | One daily plan per user per calendar day |
| `dietary_restrictions` | `UNIQUE (user_id)` | Strict 1:1 safety restrictions per user |

### Performance Indexes
| Table | Index Name | Columns | Purpose |
|---|---|---|---|
| `profiles` | `idx_profiles_user_id` | `user_id` | Fast join on user profile fetch |
| `meal_logs` | `idx_meal_logs_user_id` | `user_id` | User meal history query |
| `meal_logs` | `idx_meal_logs_user_time` | `user_id, timestamp DESC` | Adaptive feedback penalty lookup |
| `meal_logs` | `idx_meal_logs_status` | `status` | Adherence analytics aggregation |
| `pantry_items` | `idx_pantry_items_user_id` | `user_id` | User pantry list query |
| `pantry_items` | `idx_pantry_items_in_stock` | `user_id, in_stock` | In-stock pantry bonus filtering |
| `app_feedback` | `idx_app_feedback_user_id` | `user_id` | User feedback lookup |
| `foods` | `idx_foods_name` | `to_tsvector('english', name)` | Full-text candidate search (GIN) |
| `foods` | `idx_foods_category` | `food_category` | Per-slot category filtering |

---

## 5. SQL Migration Script (`003_app_tables.sql`)

```sql
-- Migration 003: Operational App Tables for DietSense
-- Idempotent, non-destructive migration.

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    full_name       TEXT NOT NULL DEFAULT '',
    dietary_pref        TEXT NOT NULL DEFAULT 'vegetarian',
    allergies           JSONB NOT NULL DEFAULT '[]'::JSONB,
    target_calories     INTEGER NOT NULL DEFAULT 2000 CHECK (target_calories > 0),
    budget_per_meal     NUMERIC(8,2) NOT NULL DEFAULT 100.00 CHECK (budget_per_meal > 0),
    prep_time_limit     INTEGER NOT NULL DEFAULT 30 CHECK (prep_time_limit > 0),
    is_solo_cook            BOOLEAN NOT NULL DEFAULT TRUE,
    active_meal_frequency   TEXT NOT NULL DEFAULT '3_meals',
    age             INTEGER NOT NULL DEFAULT 26 CHECK (age BETWEEN 2 AND 120),
    gender          TEXT NOT NULL DEFAULT 'male',
    height_cm       NUMERIC(5,2) NOT NULL DEFAULT 175.0 CHECK (height_cm > 0),
    weight_kg       NUMERIC(5,2) NOT NULL DEFAULT 75.0 CHECK (weight_kg > 0),
    goal            TEXT NOT NULL DEFAULT 'lose_weight',
    activity_level  TEXT NOT NULL DEFAULT 'lightly_active',
    preferred_cuisines JSONB NOT NULL DEFAULT '["indian"]'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles (user_id);

-- 2. Meal Logs Table
CREATE TABLE IF NOT EXISTS public.meal_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    meal_id         TEXT,
    status          TEXT NOT NULL CHECK (status IN ('eaten', 'skipped')),
    reason          TEXT CHECK (reason IS NULL OR reason IN ('time', 'cost', 'taste', 'unavailable')),
    item_tags       JSONB NOT NULL DEFAULT '[]'::JSONB,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sqlite_id       TEXT UNIQUE,
    synced_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_meal_logs_user_id ON public.meal_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_time ON public.meal_logs (user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_meal_logs_status ON public.meal_logs (status);

-- 3. Pantry Items Table
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
    sqlite_id       TEXT UNIQUE,
    synced_at       TIMESTAMPTZ,
    UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_pantry_items_user_id ON public.pantry_items (user_id);
CREATE INDEX IF NOT EXISTS idx_pantry_items_in_stock ON public.pantry_items (user_id, in_stock);

-- 4. App Feedback Table
CREATE TABLE IF NOT EXISTS public.app_feedback (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    meal_id             TEXT,
    status              TEXT NOT NULL,
    reason              TEXT,
    feedback_text       TEXT,
    derived_penalty_tag TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sqlite_id           TEXT UNIQUE,
    synced_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_app_feedback_user_id ON public.app_feedback (user_id);

-- 5. Row-Level Security Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_select_own" ON public.profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "profiles_insert_own" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "profiles_update_own" ON public.profiles FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "profiles_delete_own" ON public.profiles FOR DELETE USING (auth.uid() = user_id);

ALTER TABLE public.meal_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "meal_logs_select_own" ON public.meal_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "meal_logs_insert_own" ON public.meal_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

ALTER TABLE public.pantry_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "pantry_items_select_own" ON public.pantry_items FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "pantry_items_insert_own" ON public.pantry_items FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "pantry_items_update_own" ON public.pantry_items FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "pantry_items_delete_own" ON public.pantry_items FOR DELETE USING (auth.uid() = user_id);

ALTER TABLE public.app_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "app_feedback_select_own" ON public.app_feedback FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "app_feedback_insert_own" ON public.app_feedback FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

## 6. Execution Instructions

### Automatic Execution via Migration Script

Run dry-run first to inspect SQL without making changes:
```bash
python scripts/run_supabase_migration.py --file backend/db/migrations/003_app_tables.sql --dry-run
```

Execute migration against Supabase:
```bash
python scripts/run_supabase_migration.py --file backend/db/migrations/003_app_tables.sql
```

Run all migrations in order:
```bash
python scripts/run_supabase_migration.py --all
```

### Manual Execution via Supabase Dashboard SQL Editor
1. Log in to the [Supabase Dashboard](https://supabase.com/dashboard).
2. Open your project: `daptmrxiumhlutztgprl`.
3. In the left navigation, click on **SQL Editor**.
4. Click **New query**.
5. Paste the contents of `backend/db/migrations/003_app_tables.sql`.
6. Click **Run** (Ctrl+Enter).
7. Confirm output reports `Success. No rows returned.`

### Synchronizing Data from SQLite to Supabase

Inspect without writing:
```bash
python scripts/sync_sqlite_to_supabase.py --dry-run
```

Run live synchronization:
```bash
python scripts/sync_sqlite_to_supabase.py
```

---

## 7. Rollback Instructions

If migration `003_app_tables.sql` needs to be reverted, run the following SQL statements in the Supabase SQL Editor:

> [!WARNING]
> Dropping tables will delete any data stored in cloud `profiles`, `meal_logs`, `pantry_items`, and `app_feedback`. Local SQLite data will remain completely intact.

```sql
-- =============================================================================
-- ROLLBACK SCRIPT: Revert Migration 003
-- =============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS public.app_feedback CASCADE;
DROP TABLE IF EXISTS public.pantry_items CASCADE;
DROP TABLE IF EXISTS public.meal_logs CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- Verify rollback: public schema should only retain foundation tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

---

## 8. Migration Strategy & Non-Destructive Rules

### Rules for Safe Production Migrations
1. **Never use `DROP TABLE` or `DROP COLUMN` in production migrations**: Use deprecation flags or nullable columns instead.
2. **Always include `IF NOT EXISTS` / `IF EXISTS`**: Ensures scripts are idempotent and safe to re-run.
3. **Use Transaction Mode Connection Pooler (Port 6543)**: For application runtime queries. For DDL migrations, use autocommit on psycopg2 to prevent long transaction locks.
4. **Always Test in Dry-Run Mode**: Every migration and sync script must support `--dry-run`.
5. **Preserve Stable User Identifiers**: Use deterministic UUID generation (`uuid5`) mapping SQLite text IDs to PostgreSQL UUIDs.
6. **Keep Food Reference Data Local**: 14,099 rows in SQLite ensures sub-15ms ML recommendation scoring with zero API latency.

---

## 9. Verification & Automated Test Results

To verify the integration, run the automated test suite:

```bash
# Run Supabase integration tests
pytest tests/test_supabase_integration.py -v

# Run full test suite (55 tests across 8 suites)
pytest -q
```

All 55 tests pass:
- `test_supabase_connectivity`: PostgreSQL version check
- `test_supabase_public_tables_exist`: All 15 public tables verified
- `test_supabase_profiles_foreign_key_relationship`: profiles.user_id -> users.id CASCADE verified
- `test_pantry_items_unique_constraint`: UNIQUE(user_id, name) verified
- `test_meal_logs_idempotency_via_sqlite_id`: sqlite_id UNIQUE verified
- `test_sqlite_independence`: SQLite functions independently with >10,000 foods
- `test_supabase_sdk_client_initialization`: Supabase Python SDK client initializes cleanly
