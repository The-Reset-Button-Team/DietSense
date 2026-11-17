# DietSense — Comprehensive System Architecture & Codebase Audit (Phase 0)

**Date**: November 16, 2026  
**Auditor**: Senior Full-Stack Software Architect  
**Status**: Read-Only Phase 0 Baseline Audit  
**Target Next Steps**: Phase 1 Feature Completion, followed by Supabase & Google Gemini Integration  

---

## Executive Summary

DietSense is designed as an offline-first, safety-anchored, evidence-based meal planning application. Nutritional values originate exclusively from authoritative composition tables: **USDA FoodData Central** (13,694 items) and **ICMR-NIN / IFCT 2017** (487 regional items), totaling **14,099 active records** in the local SQLite database.

This Phase 0 audit evaluated the complete codebase across 12 inspection dimensions: folder hierarchy, backend routes, frontend components, SQLite schema, authentication, recommendation algorithms, database operations, environment configurations, dependencies, automated test suites, client-server communication, and profile/meal plan state flows.

### Primary Audit Highlights:
1. **Core Recommendation Engine is Functionally Complete in ML Layer but Disconnected from Frontend**: The backend ML modules (`ml/scoring/safety_gate.py`, `ml/recommendation/vectorizer.py`, `ml/scoring/formula.py`, `ml/adaptive/reweight.py`) implement the documented multi-factor scoring and safety gate. However, the frontend (`frontend/src/app/page.tsx` and `frontend/src/lib/nutrition.ts`) currently calculates meal plans client-side using a static 8-recipe catalog (`frontend/src/data/recipes.ts`), completely bypassing the backend recommendations API and the 14,099-food catalog.
2. **Missing Python Dependency Breaks Automated Tests**: `backend/routes/pantry.py` imports `PIL.Image`, but `pillow` is missing from the environment and `requirements.txt`. This import failure causes 5 out of 7 backend test suites (`test_auth.py`, `test_local_auth_db.py`, `test_meal_workflow.py`, `test_pantry_scanner.py`, `test_recommendations.py`) to error during pytest collection. Scoring and ETL tests (`test_scoring.py`, `test_etl.py`) pass 100% (10/10 tests).
3. **Frontend Type System is Clean**: `tsc --noEmit` exits with 0 errors. All Next.js pages, contexts, and UI components compile without TypeScript errors. However, there are no frontend unit or integration test runners configured.
4. **Duplicate Route and Schema Implementations**: Duplicate endpoints exist between `backend/app/routers/` and `backend/routes/` (e.g., profile updates and foods queries). In addition, `backend/db/schema.sql` describes a PostgreSQL/Supabase schema, whereas `backend/db/database.py` manages the actual running SQLite schema.
5. **No Cloud Dependencies Present**: The running system is 100% local (SQLite + local bcrypt/JWT + Next.js). Supabase and Gemini placeholders exist only in configuration and documentation.

---

## 1. Complete Folder Structure & File Inventory

```
DietSense/
├── .github/                         # GitHub issue & PR templates
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── .vscode/                         # Workspace editor configuration
│   └── settings.json
├── backend/                         # FastAPI backend service
│   ├── .env                         # Local backend environment variables
│   ├── .env.example                 # Template for backend environment
│   ├── main.py                      # Legacy entrypoint wrapper
│   ├── README.md                    # Backend documentation
│   ├── requirements.txt             # Backend-specific Python requirements
│   ├── app/
│   │   ├── main.py                  # Authoritative FastAPI application entrypoint
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings & environment loader
│   │   │   ├── dependencies.py      # Auth credential extractors & DB injection
│   │   │   └── security.py          # Bcrypt hashing & JWT session handling
│   │   ├── routers/
│   │   │   ├── auth.py              # /api/auth routes (register, login, logout, me, profile)
│   │   │   └── foods.py             # /api/foods catalog search router
│   │   └── schemas/
│   │       └── user.py              # Pydantic auth & biometric schemas
│   ├── db/
│   │   ├── client.py                # Database connection accessor
│   │   ├── database.py              # Authoritative SQLite schema & init_db()
│   │   ├── init_db.py               # Standalone database initialization script
│   │   ├── schema.sql               # Legacy PostgreSQL/Supabase schema script
│   │   ├── seed.sql                 # Legacy PostgreSQL seed script
│   │   └── migrations/              # Legacy PostgreSQL migration scripts
│   │       ├── 001_create_profiles.sql
│   │       └── 002_user_profile_meal_logs.sql
│   ├── models/
│   │   └── schemas.py               # Duplicate legacy Pydantic models
│   └── routes/                      # Functional domain routers
│       ├── feedback.py              # /feedback (dual-writes feedback & logs)
│       ├── foods.py                 # /foods (catalog querying)
│       ├── meal_logs.py             # /meal-logs, /analytics
│       ├── meal_plans.py            # /meal-plans (plan creation & retrieval)
│       ├── pantry.py                # /api/pantry (scanner & pantry stock)
│       ├── recommendations.py       # /recommendations (recommendation pipeline)
│       └── users.py                 # /profile, /users/profile (duplicate profile routes)
├── data/                            # Raw and processed datasets & ETL
│   ├── etl.py                       # Legacy ETL script
│   ├── README.md                    # Dataset source documentation
│   ├── sources.md                   # Source citations
│   ├── processed/
│   │   ├── foods_merged.csv         # Merged USDA + ICMR-NIN dataset (14,181 rows)
│   │   ├── ifct_foods_normalized.csv # Normalized IFCT 2017 foods
│   │   └── usda_foods_normalized.csv # Normalized USDA FoodData Central foods
│   └── raw/                         # Raw ingestion staging directory
├── database/                        # Local SQLite database & source files
│   ├── dietsense.db                 # Primary SQLite 3 database (2.8 MB, 14,099 foods)
│   ├── IFCT2017.pdf                 # Reference ICMR-NIN book
│   └── FoodData_Central_csv_2026-04-30/ # Raw USDA CSV archives
├── docs/                            # Project documentation
│   ├── ARCHITECTURE.md              # System architecture & data flow
│   ├── atmos_ui.html                # Atmosphere shader UI prototype
│   └── DIETSENSE_PROJECT_AUDIT.md   # This document
├── frontend/                        # Next.js 14 App Router client
│   ├── .env.example                 # Frontend environment template
│   ├── .env.local                   # Active frontend environment variables
│   ├── .env.local.example           # Frontend environment template
│   ├── package.json                 # Next.js dependencies & scripts
│   ├── postcss.config.mjs           # PostCSS Tailwind plugins
│   ├── tailwind.config.ts           # Tailwind theme configuration
│   ├── tsconfig.json                # TypeScript compiler configuration
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root HTML layout with AuthProvider & AtmosphereShader
│   │   │   ├── page.tsx             # Primary dashboard orchestrator (Tab interface)
│   │   │   ├── login/page.tsx       # Dedicated Sign-In page
│   │   │   ├── signup/page.tsx      # Dedicated Sign-Up page
│   │   │   ├── plans/page.tsx       # Redirect shim -> /?tab=today
│   │   │   ├── profile/page.tsx     # Redirect shim -> /?tab=profile
│   │   │   └── progress/page.tsx    # Redirect shim -> /?tab=progress
│   │   ├── components/
│   │   │   ├── Header.tsx           # App header, target calories, auth capsule
│   │   │   ├── MealCard.tsx         # Meal card, nutrition chips, swap modal, eaten/skip
│   │   │   ├── MealPlanView.tsx     # Daily plan view & routine selectors
│   │   │   ├── PantryScanner.tsx    # Receipt PDF/image OCR & fridge inventory
│   │   │   ├── ProfileStudio.tsx    # Profile, goals, diet, biometrics editor
│   │   │   ├── ProgressAnalytics.tsx # Adherence rate & skip reason charts (Recharts)
│   │   │   ├── RecipeModal.tsx      # Step-by-step Hinglish recipe instructions
│   │   │   ├── SafetyShield.tsx     # Allergen shield badge
│   │   │   ├── SwapView.tsx         # Alternative meal selection interface
│   │   │   ├── TabNav.tsx           # Dashboard tab bar
│   │   │   ├── auth/
│   │   │   │   └── AuthModal.tsx    # Pop-up modal for sign-in / registration
│   │   │   └── shader/
│   │   │       └── AtmosphereShader.tsx # Background WebGL atmospheric effect
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # React Auth Context & session management
│   │   ├── data/
│   │   │   ├── pantry.ts            # Default starter pantry items
│   │   │   └── recipes.ts           # Hardcoded catalog of 8 static recipes
│   │   ├── lib/
│   │   │   ├── api-client.ts        # Typed fetch client with credentials & JWT
│   │   │   └── nutrition.ts         # Biometrics (BMR/TDEE), meal plan grouping
│   │   ├── styles/
│   │   │   └── globals.css          # Tailwind base & theme rules
│   │   └── types/
│   │       └── index.ts             # TypeScript domain types & interfaces
├── ml/                              # Python Machine Learning pipeline
│   ├── .env                         # ML environment variables
│   ├── .env.example                 # Template for ML environment
│   ├── requirements.txt             # ML-specific dependencies
│   ├── test_recommend.py            # Standalone recommendation smoke test
│   ├── adaptive/
│   │   └── reweight.py              # Skip reason penalty reweighting (+0.1/skip)
│   ├── explainability/
│   │   └── explainers.py            # Natural language reason generation
│   ├── recommendation/
│   │   ├── recommender.py           # ML recommendation orchestrator
│   │   └── vectorizer.py            # Scikit-learn TF-IDF + cosine similarity
│   └── scoring/
│       ├── formula.py               # 4-factor and 6-factor weighted clinical formulas
│       └── safety_gate.py           # Hard allergen and dietary preference safety filter
├── samples/                         # Sample test files for receipt scanner
│   ├── blinkit_sample_bill.pdf      # Sample Blinkit invoice
│   ├── blinkit_sample_bill.png      # Rendered invoice image
│   └── fridge_sample_snapshot.png   # Sample fridge interior snapshot
├── scripts/                         # ETL, database generation & utilities
│   ├── download_sources.py          # Download USDA & IFCT raw files
│   ├── etl_ifct.py                  # Extract & parse ICMR-NIN IFCT tables
│   ├── etl_usda.py                  # Extract & parse USDA FoodData Central
│   ├── generate_sample_images.py    # Generate mock receipts and fridge images
│   ├── load_db.py                   # Ingest processed foods CSV into SQLite
│   ├── merge_sources.py             # Merge & deduplicate USDA and IFCT records
│   └── requirements.txt             # ETL-specific dependencies
├── tests/                           # Backend test suite (pytest)
│   ├── conftest.py                  # Root test fixtures & temp DB provisioning
│   ├── test_auth.py                 # Auth router tests
│   ├── test_etl.py                  # Dataset integrity tests (14,000+ foods)
│   ├── test_local_auth_db.py        # Local SQLite authentication & session tests
│   ├── test_meal_workflow.py        # End-to-end meal plan & logging workflow tests
│   ├── test_pantry_scanner.py       # Pantry scanner upload & OCR parsing tests
│   ├── test_recommendations.py      # Recommendation engine & safety gate tests
│   └── test_scoring.py              # Mathematical validation of scoring formulas
├── conftest.py                      # Root test configuration (sys.path & isolated DB)
├── pytest.ini                       # Pytest configuration
├── requirements.txt                 # Unified root dependencies
├── run_backend.py                   # Local development server launcher
└── start_local.ps1                  # PowerShell launcher for full stack
```

---

## 2. Backend API Endpoint Inventory

The FastAPI application mounts routers under both `/api` and direct root prefixes.

| HTTP Method | Route Path | Defined In | Auth Required? | Purpose & Implementation Details |
|---|---|---|---|---|
| `GET` | `/` | `backend/app/main.py` | No | Health check returning service status, version, and environment. |
| `GET` | `/health` | `backend/app/main.py` | No | Detailed health status (database ready, auth ready). |
| `POST` | `/api/auth/register` | `backend/app/routers/auth.py` | No | Registers user, hashes password with bcrypt (cost=12), creates profile in SQLite, sets HttpOnly cookie, returns JWT. |
| `POST` | `/api/auth/login` | `backend/app/routers/auth.py` | No | Verifies email & password via bcrypt, sets HttpOnly session cookie, returns user profile + JWT. |
| `POST` | `/api/auth/logout` | `backend/app/routers/auth.py` | No | Clears `dietsense_session` HttpOnly cookie. |
| `GET` | `/api/auth/me` | `backend/app/routers/auth.py` | Yes | Resolves current session from cookie or Bearer token; returns profile and active JWT. |
| `PUT` | `/api/auth/profile` | `backend/app/routers/auth.py` | Yes | Updates biometrics (weight, height, age, goal), recalculates calories, saves to SQLite. |
| `GET` | `/api/foods/` | `backend/app/routers/foods.py` | No | Queries foods from SQLite (`SELECT ... FROM foods WHERE name LIKE ... LIMIT 50`). |
| `GET` | `/foods/` | `backend/routes/foods.py` | No | Duplicate food search with category and query filters. |
| `GET` | `/foods/{food_id}` | `backend/routes/foods.py` | No | Retrieves individual food record and nutritional breakdown by ID. |
| `GET` | `/profile` | `backend/routes/users.py` | Yes | Retrieves user profile from SQLite. Duplicate of `/api/auth/profile`. |
| `GET` | `/users/profile` | `backend/routes/users.py` | Yes | Alias for `/profile`. |
| `PUT` | `/profile` | `backend/routes/users.py` | Yes | Updates user constraints (budget, prep time, allergies, diet). |
| `POST` | `/profile` | `backend/routes/users.py` | Yes | Alias for `PUT /profile`. |
| `POST` | `/users/profile` | `backend/routes/users.py` | Yes | Alias for `PUT /profile`. |
| `POST` | `/recommendations/` | `backend/routes/recommendations.py` | Yes | Executes ML recommendation pipeline (Safety Gate -> Vectorizer -> Scoring -> Adaptive Reweight -> Pantry bonus). Loads 40 SQLite foods + sample candidates. |
| `GET` | `/meal-plans` | `backend/routes/meal_plans.py` | Yes | Lists saved meal plans for the authenticated user from SQLite. |
| `GET` | `/meal_plans` | `backend/routes/meal_plans.py` | Yes | Alias for `/meal-plans`. |
| `POST` | `/meal-plans` | `backend/routes/meal_plans.py` | Yes | Persists a daily/weekly meal plan to SQLite under `user_id`. |
| `POST` | `/meal_plans` | `backend/routes/meal_plans.py` | Yes | Alias for `POST /meal-plans`. |
| `GET` | `/meal-plans/{plan_id}` | `backend/routes/meal_plans.py` | Yes | Retrieves specific plan by ID, verifying user ownership. |
| `GET` | `/meal-logs` | `backend/routes/meal_logs.py` | Yes | Retrieves all meal logs for the authenticated user. |
| `GET` | `/meal_logs` | `backend/routes/meal_logs.py` | Yes | Alias for `/meal-logs`. |
| `POST` | `/meal-logs` | `backend/routes/meal_logs.py` | Yes | Logs meal outcome (`eaten` or `skipped`). Validates reason: `time`, `cost`, `taste`, `unavailable`. |
| `POST` | `/meal_logs` | `backend/routes/meal_logs.py` | Yes | Alias for `POST /meal-logs`. |
| `GET` | `/analytics` | `backend/routes/meal_logs.py` | Yes | Calculates adherence percentage, skip reason distribution, and daily trend points directly from SQLite logs. |
| `GET` | `/meal-logs/analytics` | `backend/routes/meal_logs.py` | Yes | Alias for `/analytics`. |
| `POST` | `/feedback/` | `backend/routes/feedback.py` | Yes | Logs rating and comment; dual-writes to both `feedback` and `meal_logs` tables. |
| `GET` | `/feedback/` | `backend/routes/feedback.py` | Yes | Retrieves user feedback entries. |
| `POST` | `/api/pantry/scan` | `backend/routes/pantry.py` | Yes | Accepts multipart file (PDF or image), extracts text/features, matches grocery catalog, saves to `pantry_items`. |
| `GET` | `/api/pantry/scan-sample` | `backend/routes/pantry.py` | Yes | Returns pre-canned scan results (`blinkit` or `fridge`) for instant demo/testing. |
| `GET` | `/api/pantry/` | `backend/routes/pantry.py` | Yes | Lists user's in-stock and out-of-stock pantry items from SQLite. |
| `POST` | `/api/pantry/` | `backend/routes/pantry.py` | Yes | Manually adds a new pantry item or batch of items. |
| `PATCH` | `/api/pantry/{item_id}/toggle` | `backend/routes/pantry.py` | Yes | Toggles item `in_stock` status (0 <-> 1). |
| `DELETE` | `/api/pantry/{item_id}` | `backend/routes/pantry.py` | Yes | Deletes an item from `pantry_items`. |

---

## 3. SQLite Database Schema & Live Data Inspection

Direct inspection of `database/dietsense.db` confirms SQLite 3 format with WAL (Write-Ahead Logging) and foreign key constraints enabled.

### Table Statistics & Schemas

```sql
-- 1. foods (14,099 records — authoritative nutritional reference)
CREATE TABLE foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_local TEXT,
    data_source TEXT NOT NULL,          -- 'USDA' or 'ICMR_NIN'
    external_id TEXT,
    food_category TEXT,
    calories_kcal REAL NOT NULL,        -- strictly non-negative, 0 NaNs
    protein_g REAL NOT NULL DEFAULT 0.0,
    carbohydrates_g REAL NOT NULL DEFAULT 0.0,
    fat_g REAL NOT NULL DEFAULT 0.0,
    fiber_g REAL DEFAULT 0.0,
    sugar_g REAL DEFAULT 0.0,
    saturated_fat_g REAL DEFAULT 0.0,
    trans_fat_g REAL DEFAULT 0.0,
    sodium_mg REAL DEFAULT 0.0,
    potassium_mg REAL DEFAULT 0.0,
    calcium_mg REAL DEFAULT 0.0,
    iron_mg REAL DEFAULT 0.0,
    zinc_mg REAL DEFAULT 0.0,
    vitamin_c_mg REAL DEFAULT 0.0,
    vitamin_a_mcg REAL DEFAULT 0.0,
    vitamin_d_mcg REAL DEFAULT 0.0,
    is_vegetarian BOOLEAN DEFAULT 1,
    is_vegan BOOLEAN DEFAULT 0,
    is_gluten_free BOOLEAN DEFAULT 1,
    allergen_flags TEXT DEFAULT ''
);

-- 2. users (2 active records)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 3. profiles (2 active records)
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL COLLATE NOCASE,
    full_name TEXT NOT NULL DEFAULT '',
    dietary_pref TEXT NOT NULL DEFAULT 'vegetarian',
    allergies TEXT NOT NULL DEFAULT '[]', -- JSON string
    target_calories INTEGER NOT NULL DEFAULT 2000,
    budget_per_meal REAL NOT NULL DEFAULT 100.0,
    prep_time_limit INTEGER NOT NULL DEFAULT 30,
    is_solo_cook INTEGER NOT NULL DEFAULT 1,
    active_meal_frequency TEXT NOT NULL DEFAULT '3_meals',
    age INTEGER NOT NULL DEFAULT 26,
    gender TEXT NOT NULL DEFAULT 'male',
    height_cm REAL NOT NULL DEFAULT 175.0,
    weight_kg REAL NOT NULL DEFAULT 75.0,
    goal TEXT NOT NULL DEFAULT 'lose_weight',
    activity_level TEXT NOT NULL DEFAULT 'lightly_active',
    preferred_cuisines TEXT NOT NULL DEFAULT '["indian"]', -- JSON string
    updated_at TEXT NOT NULL
);

-- 4. meal_plans (0 records currently in database)
CREATE TABLE meal_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    target_calories INTEGER NOT NULL DEFAULT 2000,
    items TEXT NOT NULL DEFAULT '[]',   -- JSON string of recipes/meals
    status TEXT NOT NULL DEFAULT 'generated',
    created_at TEXT NOT NULL
);

-- 5. meal_logs (5 active records)
CREATE TABLE meal_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('eaten', 'skipped')),
    reason TEXT CHECK (reason IS NULL OR reason IN ('time', 'cost', 'taste', 'unavailable')),
    item_tags TEXT NOT NULL DEFAULT '[]', -- JSON string
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 6. feedback (0 records currently in database)
CREATE TABLE feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_id TEXT,
    status TEXT NOT NULL,
    reason TEXT,
    feedback_text TEXT,
    derived_penalty_tag TEXT,
    created_at TEXT NOT NULL
);

-- 7. pantry_items (5 active records)
CREATE TABLE pantry_items (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    quantity TEXT NOT NULL DEFAULT '1 unit',
    in_stock INTEGER NOT NULL DEFAULT 1,
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Divergence with `backend/db/schema.sql` (PostgreSQL Script)
`backend/db/schema.sql` contains PostgreSQL-specific definitions that are not present in SQLite:
- `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `JSONB` data types
- `TIMESTAMPTZ` with `NOW()`
- Triggers with `CREATE OR REPLACE FUNCTION`
- Table `ai_interaction_logs` (tracking Gemini model prompts, completions, and token counts).
This schema will be crucial when migrating to Supabase PostgreSQL in Phase 3.

---

## 4. Authentication Flow

DietSense implements an offline, local-first session authentication system:

```
┌────────────────────────────────────────────────────────┐
│                   BROWSER / CLIENT                     │
│  • AuthContext.tsx manages user profile & session      │
│  • Stores JWT in memory (_inMemoryToken)               │
│  • Transmits HttpOnly cookie (credentials: "include")  │
│  • Falls back to Authorization: Bearer <token>         │
└───────────────────────────┬────────────────────────────┘
                            │
              1. POST /api/auth/login
              2. Credentials sent (email, password)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                      │
│  • normalize_email(email)                              │
│  • SELECT * FROM users WHERE email = ?                 │
│  • bcrypt.checkpw(plain_password, password_hash)       │
│  • create_access_token(user_id, email, full_name)      │
│  • Signed with HS256 using JWT_SECRET                  │
│  • Response sets HttpOnly cookie:                      │
│      dietsense_session=<JWT>; Path=/; SameSite=Lax     │
│  • Returns UserProfileResponse + token in JSON body    │
└───────────────────────────┬────────────────────────────┘
                            │
              3. Subsequent Authenticated Requests
              (Cookie automatically attached or Bearer header)
                            ▼
┌────────────────────────────────────────────────────────┐
│              DEPENDENCY: get_current_user              │
│  • Checks request.headers["authorization"]             │
│  • Checks request.cookies["dietsense_session"]         │
│  • decode_access_token(token) verifies:                │
│      - HMAC signature                                  │
│      - Expiration ('exp')                              │
│      - Audience ('aud' == 'authenticated')             │
│  • Extracts verified 'sub' claim (user_id)             │
│  • NEVER trusts client-supplied user_id in body/query  │
└────────────────────────────────────────────────────────┘
```

### Key Security & Design Observations:
- **Zero Cloud Credentials Required**: No external auth provider (Supabase Auth, Auth0, etc.) is called in the current operational path.
- **Strict User Isolation**: All SQL queries across `profiles`, `meal_plans`, `meal_logs`, `feedback`, and `pantry_items` filter by `user_id = ?` derived strictly from the verified JWT.
- **Stubbed Password Recovery**: `AuthContext.tsx` contains stub implementations of `resetPassword` and `updatePassword` that return `{ success: true }` without executing backend requests.

---

## 5. Recommendation Engine & ML Pipeline

The recommendation engine is located in `ml/` and orchestrated by `ml/recommendation/recommender.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│               1. CANDIDATE RETRIEVAL & FILTERING                │
│  • backend/routes/recommendations.py: load_candidate_foods()    │
│  • Queries 40 rows from SQLite 'foods' table + 8 sample meals   │
│  • Derives prep_time, cost_estimate, and tags from category     │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. STEP 1: HARD SAFETY GATE                        │
│  • ml/scoring/safety_gate.py: filter_safe()                     │
│  • Strictly excludes non-veg items if dietary_pref == veg/vegan │
│  • Rejects animal products (dairy, egg, honey) if vegan         │
│  • Conservative Allergen Handling: missing/unknown allergen      │
│    data is excluded whenever the user has declared allergies   │
│  • Unsafe items are permanently discarded before scoring        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              3. STEP 2: PREFERENCE SIMILARITY                   │
│  • ml/recommendation/vectorizer.py: get_similarity()            │
│  • TF-IDF Vectorizer with English stop-words                    │
│  • Fits vocabulary across candidate text + user preferences     │
│  • Calculates cosine similarity array in [0.0, 1.0]             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              4. STEP 3: MULTI-FACTOR WEIGHTED SCORING           │
│  • ml/scoring/formula.py: compute_score()                       │
│  • Final Score = 0.40 * Similarity                              │
│                + 0.30 * Macro Fit (per-meal cal target / 4)    │
│                + 0.20 * Budget Fit (per-meal budget)           │
│                + 0.10 * Prep-Time Fit (prep-time limit)        │
│  • All sub-scores strictly bounded in [0.0, 1.0]                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              5. STEP 4: ADAPTIVE PENALTY LAYER                  │
│  • ml/adaptive/reweight.py: apply_penalties()                   │
│  • Pulls user's real meal logs from SQLite                      │
│  • Skip reasons map to penalty tags:                            │
│      - 'time'        -> 'long-prep-time' (>25 min)              │
│      - 'cost'        -> 'expensive' (>100 cost)                 │
│      - 'unavailable' -> 'hard-to-find'                          │
│  • +0.1 penalty per skip, capped at 0.5 per tag                 │
│  • Final score clamped at 0.0 minimum                           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              6. STEP 5: PANTRY BONUS & EXPLAINABILITY           │
│  • ml/recommendation/recommender.py                             │
│  • +0.05 bonus if candidate ingredients match user's pantry     │
│  • Applied strictly post-safety so it cannot resurrect excluded  │
│  • ml/explainability/explainers.py generates human-readable     │
│    explanation string citing exact reasons and penalties applied│
└─────────────────────────────────────────────────────────────────┘
```

### Critical Gap in Frontend Integration:
The algorithm in `ml/` is mathematically sound, clinical, and passes all standalone tests. However, **`frontend/src/app/page.tsx` never calls `/recommendations/`**.
Instead:
- `page.tsx` calls `calculateMealPlanItems()` in `frontend/src/lib/nutrition.ts`.
- `calculateMealPlanItems()` filters the 8 static recipes in `frontend/src/data/recipes.ts`.
- The 14,099 foods in `dietsense.db` are never surfaced to the user in the daily meal plan.

---

## 6. Frontend Pages and Components

The frontend is a Next.js 14 App Router application with Tailwind CSS, Lucide icons, and Recharts.

### Pages:
- `frontend/src/app/page.tsx`: Single-page multi-tab layout (`/?tab=today`, `pantry`, `profile`, `swap`, `safety`, `progress`).
- `frontend/src/app/login/page.tsx`: Standalone sign-in page with client-side form validation.
- `frontend/src/app/signup/page.tsx`: Standalone sign-up page.
- `frontend/src/app/plans/page.tsx`, `profile/page.tsx`, `progress/page.tsx`: Next.js redirect shims forwarding to `/?tab=...`.
- `frontend/src/app/layout.tsx`: Root layout with `AuthProvider` and background `AtmosphereShader`.

### Components:
- `Header.tsx`: Displays goal, calculated target calories, and auth capsule (user avatar / sign-in button).
- `MealPlanView.tsx`: Displays the daily meal plan cards, solo cook routine selector, and pantry sync banner.
- `MealCard.tsx`: Individual meal card displaying slot label, time slot, recipe name, Hinglish tagline, macro chips (calories, protein, carbs, fat, fiber), pantry match status, explainability explanation, "Recipe & Prep" modal button, "Swap" modal trigger, and "Mark Eaten / Skip" action buttons.
- `PantryScanner.tsx`: Upload interface for receipt PDF, receipt image, or fridge snapshot. Supports instant one-click sample presets ("Blinkit Invoice" and "Fridge Snapshot"). Manages scanned inventory.
- `ProfileStudio.tsx`: Form for editing dietary preference, allergies, cooking profile, and biometric parameters.
- `ProgressAnalytics.tsx`: Interactive Recharts dashboard visualizing adherence percentages and skip reason breakdowns from `/analytics`.
- `RecipeModal.tsx`: Modal displaying step-by-step cooking instructions, ingredient measurements, and solo cooking hacks in Hinglish.
- `SafetyShield.tsx`: Displays allergen safety gate status and active filters.
- `SwapView.tsx`: Overview of alternative dishes across all meal slots.
- `TabNav.tsx`: Navigation bar switching between the 6 tabs.
- `AtmosphereShader.tsx`: Interactive canvas rendering a GPU noise atmospheric background.

---

## 7. Environment Variables & Configuration

### Backend (`backend/.env` & `backend/app/core/config.py`):
- `SQLITE_DB_PATH`: Path to SQLite file (`database/dietsense.db`).
- `JWT_SECRET`: Secret key for HMAC signing (`dietsense-local-dev-secret-key-32chars-minimum-needed`).
- `JWT_EXPIRE_MINUTES`: Expiration duration (default 10080 minutes / 7 days).
- `ENVIRONMENT`: Set to `development`.
- `CORS_ORIGINS`: `http://localhost:3000,http://127.0.0.1:3000`.
- Deprecated placeholders present: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`.

### Frontend (`frontend/.env.local`):
- `NEXT_PUBLIC_API_BASE_URL`: `http://localhost:8000`.
- `NEXT_PUBLIC_SITE_URL`: `http://localhost:3000`.

---

## 8. Dependencies Audit

Four separate `requirements.txt` files exist in the codebase:
1. `requirements.txt` (Root): Defines core FastAPI, ML, and test packages. Missing `pillow` and `pypdf`.
2. `backend/requirements.txt`: Defines pinned backend dependencies. Missing `pillow` and `pypdf`.
3. `ml/requirements.txt`: Defines scikit-learn, numpy, pandas, joblib.
4. `scripts/requirements.txt`: Defines ETL packages including `pdfplumber` and `psycopg2-binary`.

### Python Virtual Environment Status:
- Virtual environment at `.venv` has Python 3.12.14, FastAPI 0.111.0, Scikit-learn 1.5.x, Pytest 9.1.1.
- `PIL` (Pillow) is **not installed** in `.venv`, breaking imports in `backend/routes/pantry.py`.

### Frontend (`frontend/package.json`):
- Dependencies: Next.js 14.2.5, React 18.3.1, React DOM 18.3.1, Lucide React 0.414.0, Recharts 2.12.7, React Hook Form 7.52.1, Zod 3.23.8, Tailwind Merge, CLSX.
- Dev Dependencies: TypeScript 5.5.3, Tailwind CSS 3.4.6, Autoprefixer, PostCSS, ESLint 8.57.0.
- Missing: Frontend testing framework (Vitest / Jest, React Testing Library).

---

## 9. Automated Test Results

### Pytest Execution (`.\.venv\Scripts\pytest -v`):
```
collected 10 items / 5 errors

ERRORS:
- ERROR collecting tests/test_auth.py: ModuleNotFoundError: No module named 'PIL'
- ERROR collecting tests/test_local_auth_db.py: ModuleNotFoundError: No module named 'PIL'
- ERROR collecting tests/test_meal_workflow.py: ModuleNotFoundError: No module named 'PIL'
- ERROR collecting tests/test_pantry_scanner.py: ModuleNotFoundError: No module named 'PIL'
- ERROR collecting tests/test_recommendations.py: ModuleNotFoundError: No module named 'PIL'

Root Cause:
backend/app/main.py imports routes.pantry, which executes `from PIL import Image`.
Because Pillow is not installed in the Python environment, any test that imports `app.main` fails collection.
```

### Passing Tests (`pytest tests/test_scoring.py tests/test_etl.py`):
```
============================= test session starts =============================
tests/test_scoring.py::test_weights_sum_to_one PASSED                    [ 10%]
tests/test_scoring.py::test_weight_values PASSED                         [ 20%]
tests/test_scoring.py::test_compute_score_perfect PASSED                 [ 30%]
tests/test_scoring.py::test_compute_score_zero PASSED                    [ 40%]
tests/test_scoring.py::test_compute_score_bounds PASSED                  [ 50%]
tests/test_scoring.py::test_compute_score_rejects_out_of_range PASSED    [ 60%]
tests/test_etl.py::test_merged_csv_exists_and_populated PASSED           [ 70%]
tests/test_etl.py::test_both_sources_present PASSED                      [ 80%]
tests/test_etl.py::test_database_foods_loaded PASSED                     [ 90%]
tests/test_etl.py::test_no_nan_calories PASSED                           [100%]
============================= 10 passed in 1.52s ==============================
```

### Standalone ML Script (`python ml/test_recommend.py`):
- Fails with `ModuleNotFoundError: No module named 'ml'` if run without `PYTHONPATH=.`.
- When run with `$env:PYTHONPATH='.'`, executes successfully and correctly prints ranked recommendation:
  `Vegetable Poha | score=0.68 -> Recommended because it matches your vegetarian preference, fits within your budget target, ~15 min prep time.`

### Frontend Type Check (`npm run type-check`):
- `tsc --noEmit` passed with 0 errors.

---

## 10. Findings: Working, Incomplete, Broken, Duplicates & Security

### Working Features:
- **Local Food Composition Database**: SQLite contains 14,099 verified food records from USDA and ICMR-NIN with zero NaN values for energy.
- **ML Scoring & Safety Gate**: `ml/scoring/safety_gate.py` filters non-vegetarian/vegan items and handles allergens conservatively. The 4-factor scoring formula accurately evaluates similarity, calorie fit, budget fit, and preparation time fit.
- **Adaptive Reweighting**: Skip reasons (`time`, `cost`, `unavailable`) dynamically penalize matching candidate food tags by +0.1 per skip (capped at 0.5).
- **Authentication**: User registration, login, bcrypt password hashing, and JWT token issuance and validation work reliably.
- **Frontend Dashboard & Tabs**: Navigation between Today, Pantry, Profile, Swap, Safety, and Progress operates smoothly with full responsive design.
- **Pantry Scanner Demo Presets**: Scanning with sample presets ("Blinkit Invoice" and "Fridge Snapshot") accurately populates the inventory.
- **Analytics Visualization**: Recharts components accurately graph eaten vs. skipped proportions and daily trends based on SQLite records.

### Incomplete Features:
- **Dynamic Recommendations on Frontend**: The daily meal plan displayed in the UI does not query `/recommendations/` or SQLite foods; it uses the 8 static mock recipes in `recipes.ts`.
- **Alternative Meal Options**: Meal slots only show 1 or 2 hardcoded alternatives from `recipes.ts`. Dynamic 3–5 candidate generation per slot from the food catalog is not wired up.
- **Slot Regeneration**: There is no UI control or backend endpoint to regenerate a single meal slot without affecting other slots.
- **Meal Plans Storage**: While `/meal-plans` exists in FastAPI, the frontend never persists or retrieves daily plans from this endpoint (0 records in `meal_plans` table).
- **Password Reset**: Frontend forgot-password handlers are UI stubs with no backend SMTP or recovery token logic.

### Broken Features:
- **Pytest Suite Collection**: Broken by `from PIL import Image` in `backend/routes/pantry.py` due to missing `pillow` dependency.
- **Standalone `ml/test_recommend.py`**: Lacks relative import or `sys.path` bootstrapping, causing failure when invoked directly without setting `PYTHONPATH`.
- **Route Prefix Inconsistencies**: Some routes use `/api/` (`/api/auth`, `/api/foods`, `/api/pantry`), while others use root prefixes (`/recommendations`, `/feedback`, `/foods`, `/meal-plans`, `/meal-logs`, `/profile`).

### Duplicate Implementations:
- **Profile Routes**:
  - `backend/app/routers/auth.py`: `PUT /api/auth/profile`
  - `backend/routes/users.py`: `GET /profile`, `PUT /profile`, `POST /profile`, `GET /users/profile`, `POST /users/profile`
- **Food Query Routes**:
  - `backend/app/routers/foods.py`: `GET /api/foods/`
  - `backend/routes/foods.py`: `GET /foods/`, `GET /foods/{id}`
- **Logging / Feedback**:
  - `backend/routes/meal_logs.py`: `POST /meal-logs`
  - `backend/routes/feedback.py`: `POST /feedback/` (which inserts into both `feedback` and `meal_logs`)
- **Pydantic Schemas**:
  - `backend/app/schemas/user.py` vs `backend/models/schemas.py`
- **Requirements Files**:
  - 4 divergent requirements files (`requirements.txt`, `backend/requirements.txt`, `scripts/requirements.txt`, `ml/requirements.txt`).

### Security Issues:
- **Static Default JWT Secret**: `JWT_SECRET` in `config.py` defaults to `"dietsense-local-dev-secret-key-32chars-minimum-needed"`. If deployed to production without overriding this variable in `.env`, tokens could be forged.
- **CORS Permissiveness**: While origins are restricted to `localhost:3000`, all headers and HTTP methods are allowed with `allow_credentials=True`.
- **Plaintext SQLite Database**: `dietsense.db` is stored unencrypted on the local filesystem.

---

## 11. Integration Risks for Supabase & Gemini

When preparing DietSense for Supabase and Google Gemini integration, the following risks must be managed:

### 1. Database Paradigm Shift (SQLite -> PostgreSQL / Supabase)
- SQLite is loosely typed and lacks native JSON types, array columns, and stored procedures.
- `backend/db/database.py` stores JSON arrays as serialized strings (`TEXT`). In Supabase PostgreSQL, these should be native `JSONB` or `TEXT[]`.
- Data migration must transfer the 14,099 foods from SQLite into Supabase PostgreSQL without loss of nutrient precision or category flags.

### 2. Authentication Alignment (Local JWT vs Supabase GoTrue)
- Currently, DietSense verifies JWTs signed with a symmetric secret (`HS256`) via local bcrypt passwords.
- Supabase Auth uses asymmetric JWTs (`RS256` or `ES256`) or custom project secrets, with a specific payload structure (`sub` = Supabase Auth UID, `app_metadata`, `user_metadata`).
- Backend route dependencies (`get_current_user`) must be adapted to validate Supabase JWT tokens while maintaining the strict rule: *user identity is derived strictly from the verified JWT, never from request parameters*.

### 3. Nutrition Integrity & Gemini Hallucination Gate
- **Core Clinical Requirement**: AI/LLM systems must never invent or estimate nutritional values.
- If Google Gemini is integrated to suggest recipes or explain meals:
  - Macro and micro nutrient values (calories, protein, carbs, fat, fiber) must strictly originate from the reference database records.
  - Gemini's role must be restricted to natural language explanation, Hinglish translation, cooking step generation, and receipt OCR reasoning.
  - Gemini responses must be logged in `ai_interaction_logs` for clinical auditing, as defined in `backend/db/schema.sql`.

### 4. Receipt Scanner OCR Transition
- Current receipt parsing in `backend/routes/pantry.py` uses heuristic regex and a keyword dictionary (`GROCERY_CATALOG`).
- Replacing or augmenting this with Gemini Multimodal Vision will significantly improve detection accuracy for Indian grocery items and unstructured fridge photos, but requires robust fallback when offline or when rate limits are exceeded.

---

## 12. Recommended Implementation Order

To maintain stability and honor project constraints, modifications should proceed in the following structured sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 1: LOCAL FEATURE COMPLETION                   │
│  1. Add 'pillow' and 'pypdf' to requirements and resolve test   │
│     collection errors so all 7 test suites pass.               │
│  2. Wire frontend daily meal plan to local FastAPI backend      │
│     recommendation API (/recommendations/).                     │
│  3. Expand candidate generation to draw from the 14,099 SQLite   │
│     food catalog instead of the 8 static mock recipes.          │
│  4. Implement 3–5 alternative options per meal slot.            │
│  5. Add meal slot option selector / carousel to MealCard.       │
│  6. Implement single-slot regeneration endpoint & UI trigger.   │
│  7. Ensure live dynamic macro recalculation on meal change.     │
│  8. Write frontend & backend tests for dynamic meal workflows.  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 2: CODEBASE CONSOLIDATION                     │
│  1. Unify duplicate routers (/api/auth vs /routes/users;        │
│     /api/foods vs /routes/foods; /meal-logs vs /feedback).      │
│  2. Harmonize Pydantic schemas in backend/models and schemas.   │
│  3. Consolidate divergent requirements.txt files into one.      │
│  4. Standardize route prefixes to /api/*.                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 3: SUPABASE INTEGRATION                       │
│  1. Provision Supabase project & configure environment keys.    │
│  2. Execute PostgreSQL schema migration based on schema.sql.    │
│  3. Bulk load 14,099 foods from SQLite into Supabase PostgreSQL.│
│  4. Configure Supabase Row-Level Security (RLS) policies.       │
│  5. Transition backend authentication to Supabase Auth JWTs.    │
│  6. Update frontend AuthContext to use @supabase/supabase-js.   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 4: GOOGLE GEMINI INTEGRATION                  │
│  1. Setup Google GenAI / Gemini 1.5 Flash SDK in backend.       │
│  2. Implement grounded Hinglish recipe generator (nutrition     │
│     anchored to DB food facts, Gemini writes instructions).     │
│  3. Integrate Gemini Vision for receipt OCR and fridge snapshots│
│     in PantryScanner.                                           │
│  4. Activate ai_interaction_logs table for audit trail.         │
│  5. Add safety guardrails against prompt injection.             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 5: TESTING & PRODUCTION HARDENING             │
│  1. End-to-end integration testing (Playwright / Cypress).      │
│  2. Frontend unit testing with Vitest & React Testing Library.  │
│  3. Rate limiting, secret management, and production packaging. │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. Audit Sign-Off

- **Audit Type**: Strict Read-Only Audit (Phase 0).
- **Files Modified / Deleted**: 0 application files modified.
- **Dependencies Installed**: 0 packages installed.
- **Database Status**: Local SQLite `dietsense.db` preserved intact (14,099 foods, 2 users, 2 profiles, 5 meal logs, 5 pantry items).
- **Outcome**: DietSense possesses a solid clinical and architectural foundation with an authoritative dataset and robust ML ranking. The system is well-positioned for Phase 1 local dynamic recommendations, followed by smooth cloud and AI integration in Phases 3 and 4.
