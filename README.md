# DietSense — Adaptive AI Meal Planning System

> Evidence-based, explainable, personalized meal planning powered by USDA and ICMR-NIN nutrition data, Scikit-learn, FastAPI, Next.js, and Google Gemini AI.

[![Build & Test Status](https://img.shields.io/badge/Pytest-185%20Passed-brightgreen)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Offline--First%20SQLite%20%2B%20Supabase%20Sync-blue)](ARCHITECTURE.md)
[![AI Engine](https://img.shields.io/badge/AI-Gemini%203.8%20Flash%20%2B%20Offline%20Fallback-orange)](docs/GEMINI_BACKEND_IMPLEMENTATION.md)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20App%20Router-black)](frontend/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## Project Overview and Core Principles

DietSense is an adaptive, safety-anchored meal planning and nutrition recommendation platform designed to deliver personalized, transparent, and clinically grounded dietary plans.

### Non-Negotiable Core Principles
1. **Authoritative Nutrition Data:** Calorie and macronutrient values are derived strictly from authoritative food composition tables (USDA FoodData Central and ICMR-NIN / IFCT 2017, totaling 14,099 verified items). Generative AI never predicts, alters, or hallucinates nutrition numbers.
2. **Hard Safety Gate Runs First:** Strict dietary constraints (vegetarian, vegan, pescatarian) and allergen exclusions (peanuts, tree nuts, dairy, gluten, eggs, fish, shellfish, soy) execute before any scoring occurs. Boosts or penalties can never re-introduce an excluded item.
3. **Deterministic & Explainable Scoring:** Candidate meals are ranked using transparent multi-factor scoring:
   $$\text{Score} = 0.30 \times \text{MacroFit} + 0.20 \times \text{GoalFit} + 0.20 \times \text{PrefFit} + 0.15 \times \text{FeedbackFit} + 0.10 \times \text{Diversity} + 0.05 \times \text{PrepTime}$$
4. **Adaptive Feedback Loop:** When a user logs a meal as *skipped*, DietSense infers the underlying reason (*time* for long prep time, *cost* for expensive ingredients) to gently apply penalties to matching candidates in future recommendations (+0.1 per skip, capped at 0.5).
5. **Non-Medical Disclaimer:** DietSense is a lifestyle decision-support system, not a clinical diagnostic medical device. Every AI-assisted view carries clear medical disclaimers.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               LOCAL FOOD CATALOG & ETL                      │
│                                                             │
│   USDA FoodData Central (13,694 foods)                      │
│   ICMR-NIN / IFCT 2017  (487 foods)                         │
│             ↓                                               │
│   ETL Pipeline (Pandas: clean units, verify 0 NaNs)         │
│   Saved to database/dietsense.db (14,099 verified foods)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND API                         │
│                                                             │
│   • Local SQLite Database (database/dietsense.db)           │
│     Tables: users, profiles, auth_identities, meal_plans,   │
│             meal_logs, feedback, pantry_items, sync_queue   │
│   • Dual-Database Sync: SQLite <-> Supabase PostgreSQL      │
│   • Strict user data isolation on every query (0 IDOR)      │
│   • Protected Endpoints: /api/auth, /api/foods,             │
│       /api/recommendations, /api/meal-plans, /api/pantry,   │
│       /api/ai, /api/sync                                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             MACHINE LEARNING & SCORING                      │
│                                                             │
│   1. Hard Safety Gate: Allergen & dietary exclusion floor   │
│   2. Text Vectorization: TF-IDF + Cosine similarity         │
│   3. 6-Factor Multi-Scoring: Macro (30%), Goal (20%),       │
│      Pref (20%), Feedback (15%), Diversity (10%), Prep (5%) │
│   4. Dynamic Meal Swapping with macro deltas & match %      │
│   5. Google Gemini 3.8 Flash AI with Offline Fallbacks      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  NEXT.JS 14 FRONTEND                        │
│                                                             │
│   • Next.js 14 App Router + React 18 + TypeScript + Tailwind│
│   • Atmosphere UI: Meal Plan Grid, Profile Studio, Progress │
│   • Dynamic Meal Swap View with safety validation           │
│   • Interactive Cook Mode with timers and checklists        │
│   • Multimodal Pantry Scanner (Receipt OCR & Fridge Photo)  │
│   • PDF / WhatsApp / Text Meal Plan Export                  │
│   • Running locally on http://localhost:3000                │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start (Local Setup)

The entire system can run locally on your machine with zero external cloud accounts.

### 1. Prerequisites
- Python: 3.10, 3.11, or 3.12 (Python 3.12 recommended)
- Node.js: 18.x or 20.x LTS
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/The-Reset-Button-Team/DietSense-.git
cd DietSense-
```

### 3. One-Click Start (Windows PowerShell)
```powershell
.\start_local.ps1
```
This script automatically detects your `.venv`, initializes the local SQLite database, and launches both the backend and frontend in parallel.

### 4. Or Run Manually:

#### A. Initialize Database and Start Backend
```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate # On macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize SQLite database schema
python backend/db/init_db.py

# 4. Launch FastAPI backend
python run_backend.py
# Backend running at: http://127.0.0.1:8000
# Swagger API Docs:  http://127.0.0.1:8000/docs
```

#### B. Start Frontend
```bash
# In a separate terminal:
cd frontend
npm install
npm run dev
# Frontend running at: http://localhost:3000
```

---

## Operation Modes and Configuration

DietSense supports two operational modes:

### Mode 1: 100% Local-Only Operation (Offline-First)
- Uses local SQLite (`database/dietsense.db`).
- Uses local bcrypt password hashing and HS256 JWT sessions.
- Generative AI calls seamlessly fall back to deterministic rule-based algorithms (`backend/app/ai/fallback.py`).
- No external internet connection or third-party API keys required.

### Mode 2: Cloud-Enabled Operation (Supabase + Google Gemini)
Enable cloud synchronization and generative AI by populating `backend/.env`:

```env
# Local Database
DATABASE_PROVIDER=sqlite
SQLITE_DB_PATH=database/dietsense.db

# Supabase Cloud Synchronization
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_DB_URL=postgresql://postgres.your-project:password@aws-0-region.pooler.supabase.com:6543/postgres

# Google Gemini Generative AI
GEMINI_API_KEY=your-google-ai-studio-api-key
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite
GEMINI_REQUEST_TIMEOUT=12.0
GEMINI_MAX_RETRIES=3
GEMINI_RATE_LIMIT_RPM=60
AI_FEATURE_ENABLED=true
```

Run Supabase migrations:
```bash
python backend/db/migrations/004_auth_identities.py
python backend/db/migrations/005_sync_tables.py
```

---

## Testing and Verification

DietSense maintains a comprehensive automated testing suite with 100% pass rate:

### 1. Backend Automated Tests (Pytest)
```bash
pytest tests/ -v
```
185 passed across 18 test suites:
- `test_auth.py`: JWT headers, signatures, audience, expiry validation
- `test_local_auth_db.py`: SQLite persistence, bcrypt registration, user isolation
- `test_phase3_supabase_auth.py`: Supabase token mapping, account linking, conflict rejection
- `test_supabase_integration.py`: Cloud PostgreSQL schema, RLS policies, idempotency
- `test_phase4_sync.py`: Mutation queue, retry backoff, Last-Write-Wins conflict resolution
- `test_scoring.py`: Mathematical weights, score bounds, zero-score edge cases
- `test_recommendations.py`: Top-N generation, safety floor, pantry bonuses
- `test_daily_recommendations.py`: Daily meal plan slots, per-slot shuffling, macro totals
- `test_slot_recommendations.py`: Slot queries, nutritional data completeness
- `test_phase8b_swap_and_safety.py`: Dynamic swapping, macro deltas, safety shield
- `test_phase8c_meal_plans_and_profile.py`: 7-day meal plan persistence, profile updates
- `test_phase8d_ml_enhancements.py`: Feature vectorizer, adaptive penalties, reweighting
- `test_phase8e_pantry_intelligence.py`: Receipt bill OCR, freshness indicators, recipe matching
- `test_phase8f_export_and_cooking.py`: PDF export, WhatsApp export, Cook Mode step-by-step
- `test_pantry_scanner.py`: PDF receipt parsing, fridge photo scanning
- `test_meal_workflow.py`: Complete meal logging, skips, adaptive re-ranking
- `test_gemini_backend.py`: Gemini assistant, rate limiter, timeouts, offline fallbacks
- `test_gemini_frontend_contract.py`: Frontend contract verification, zero client key leaks
- `test_etl.py`: Merged USDA and ICMR-NIN dataset integrity (0 NaNs)

### 2. Frontend Validation
```bash
cd frontend
npm run type-check   # Strict TypeScript compiler verification (0 errors)
npm run lint         # ESLint check (0 warnings)
npm run build        # Production Next.js 14 build (10/10 static routes)
```

---

## Dataset Provenance

| Dataset | Records | Description | Usage in DietSense |
|---------|---------|-------------|--------------------|
| **USDA FoodData Central** | 13,694 | Foundation Foods and SR Legacy reference nutrients | Baseline macro and micronutrient clinical benchmarks |
| **ICMR-NIN / IFCT 2017** | 487 | Indian Food Composition Tables (National Institute of Nutrition) | Regional Indian recipes, staples, and traditional dishes |
| **Total Merged Catalog** | **14,099** | Unified food database (`database/dietsense.db`) | 100% clinically verified, zero hallucinated nutrition values |

---

## Documentation Links

- [`docs/DIETSENSE_FINAL_IMPLEMENTATION_GUIDE.md`](docs/DIETSENSE_FINAL_IMPLEMENTATION_GUIDE.md) — Comprehensive Phase 10 integration, operation, and demonstration guide
- [`docs/DIETSENSE_FINAL_TEST_REPORT.md`](docs/DIETSENSE_FINAL_TEST_REPORT.md) — Complete Phase 9 security and testing audit report (185/185 passed)
- [`docs/DIETSENSE_SYNC_IMPLEMENTATION.md`](docs/DIETSENSE_SYNC_IMPLEMENTATION.md) — Cloud synchronization and conflict resolution architecture
- [`docs/GEMINI_BACKEND_IMPLEMENTATION.md`](docs/GEMINI_BACKEND_IMPLEMENTATION.md) — Generative AI architecture, prompts, and safety fallback
- [`docs/SUPABASE_DATABASE_MIGRATION_GUIDE.md`](docs/SUPABASE_DATABASE_MIGRATION_GUIDE.md) — PostgreSQL migrations, RLS policies, and triggers
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Core system architecture and data flow maps
