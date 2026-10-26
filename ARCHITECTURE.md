# DietSense — Technical Architecture

## 1. System Overview

DietSense is an **offline-first, safety-anchored, evidence-based** adaptive meal planning and recommendation system.
All nutritional values originate exclusively from authoritative food composition tables (**USDA FoodData Central** and **ICMR-NIN / IFCT 2017**). The recommendation engine applies rule-based constraints and explainable scoring to ensure recommendations are safe, transparent, and auditable.

---

## 2. End-to-End Architecture & Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                   DATA INGESTION LAYER (M4)                      │
│                                                                  │
│  • USDA FoodData Central (13,694 reference food items)           │
│  • ICMR-NIN / IFCT 2017 (487 regional Indian food items)         │
│  • Total: 14,181 foods, 0 NaN energy values                      │
│  • ETL Pipeline: scripts/etl_usda.py, scripts/etl_ifct.py,       │
│                  scripts/merge_sources.py, scripts/load_db.py     │
│  • Stored in: data/processed/foods_merged.csv & SQLite           │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                 LOCAL SQLITE DATABASE (M2)                       │
│                                                                  │
│  Database file: database/dietsense.db                            │
│  Schema management: backend/db/database.py & init_db.py          │
│                                                                  │
│  Tables:                                                         │
│  ├── foods               (14,181 nutrition records)              │
│  ├── users               (id, email, password_hash, created_at)  │
│  ├── profiles            (dietary_pref, allergies, targets)     │
│  ├── meal_plans          (saved user daily plans)                │
│  ├── meal_logs           (outcome: eaten/skipped, skip reason)   │
│  ├── feedback            (ratings, notes)                        │
│  └── pantry_items        (ingredients in stock, quantities)      │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND API (M2)                       │
│                                                                  │
│  • Local authentication: /api/auth/register, /login, /me, /logout│
│  • Security: Bcrypt password hashing + signed session JWTs       │
│  • Isolation: Every query filters strictly by verified user_id    │
│  • Business routes: /api/recommendations, /api/meal-logs,         │
│                     /api/meal-plans, /api/pantry                 │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│         RECOMMENDATION ENGINE & SAFETY PIPELINE (M3)             │
│                                                                  │
│  Step 1: Hard Safety Gate (ml/scoring/safety_gate.py)            │
│          • Checks vegetarian, vegan, and allergen declarations   │
│          • Missing allergen information is excluded (safe mode)  │
│          • Runs BEFORE any scoring; cannot be overridden         │
│                                                                  │
│  Step 2: Preference Similarity (ml/recommendation/vectorizer.py) │
│          • TF-IDF vectorization + Cosine similarity (Weight 0.4) │
│                                                                  │
│  Step 3: Multi-Factor Weighted Scoring (ml/scoring/formula.py)   │
│          • Base Score = 0.40 × Similarity                        │
│                       + 0.30 × Macronutrient Fit                 │
│                       + 0.20 × Budget Fit                        │
│                       + 0.10 × Prep-Time Fit                     │
│                                                                  │
│  Step 4: Adaptive Penalty Layer (ml/adaptive/reweight.py)        │
│          • Skip reasons map to penalty tags:                     │
│            - "time"        → long-prep-time                      │
│            - "cost"        → expensive                           │
│            - "unavailable" → hard-to-find                        │
│          • +0.1 penalty per skip, capped at 0.5 per tag          │
│          • Final score clamped at 0.0                            │
│                                                                  │
│  Step 5: Pantry Boost & Explainability                           │
│          • Boost for matching items detected in user pantry      │
│          • Human-readable reasons generated from real factors    │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                     NEXT.JS FRONTEND (M1)                        │
│                                                                  │
│  • Next.js App Router + TypeScript + Tailwind CSS                │
│  • Meal cards with real USDA/ICMR-NIN nutrition + score reasons  │
│  • Pantry Scanner (Receipt PDF/Image OCR & Fridge Snapshots)     │
│  • Interactive Recharts analytics (adherence %, skip reasons)    │
│  • Zero cloud credentials required in browser                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Entity Relationship (Local SQLite)

All tables use parameterized SQL with strict user isolation:

```
 users (id PK)
   │
   ├──< profiles (id PK, user_id FK -> users.id)
   ├──< meal_plans (id PK, user_id FK -> users.id)
   ├──< meal_logs (id PK, user_id FK -> users.id)
   ├──< feedback (id PK, user_id FK -> users.id)
   └──< pantry_items (id PK, user_id FK -> users.id)

 foods (id PK, external_id, name, data_source, calories_kcal, ...)
```

---

## 4. Key Design Decisions

1. **Why Local SQLite instead of Cloud Supabase?**
   - Eliminates all external cloud dependencies, API key requirements, and network latency.
   - Complete data privacy and auditability on a single workstation.
   - Zero cost and offline operational capability.

2. **Why Safety Gate before Scoring?**
   - Safety is a non-negotiable boolean decision (yes/no).
   - Scoring is a continuous optimization ([0.0, 1.0]).
   - If scoring ran first, high similarity or pantry boosts could improperly outrank allergen risks. By filtering first, unsafe foods are irrevocably eliminated.

3. **Why Deterministic Scoring instead of Black-Box Deep Learning?**
   - Nutrition recommendations require clinical defensibility and explainability.
   - Every recommendation comes with transparent reasons tied to its exact sub-scores.
   - Changes in user skip history immediately and predictably reflect in the next ranked list.
