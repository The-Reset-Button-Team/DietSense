# DietSense — Technical Architecture

## 1. System Overview

DietSense is a **safety-first, evidence-based** adaptive meal planning system. All nutritional calculations are anchored to authoritative datasets. The AI layer provides natural-language explanations only — it never originates or modifies nutrition numbers.

---

## 2. Full Data Flow Pipeline

```
┌─────────────────────────────────────────────────────┐
│           DATA INGESTION LAYER (Member 4)           │
│                                                     │
│  USDA FoodData Central (CSV)                        │
│  ICMR-NIN / IFCT 2017 (PDF → extracted)             │
│  WHO Dietary Guidelines (reference)                 │
│         ↓                                           │
│  scripts/etl_usda.py   scripts/etl_ifct.py          │
│  (Pandas: clean, normalize kcal/g, deduplicate)     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│          POSTGRESQL DATABASE (Member 2)             │
│                                                     │
│  foods │ recipes │ recipe_ingredients               │
│  users │ dietary_restrictions                       │
│  meal_plans │ meal_plan_items                       │
│  user_feedback │ preference_weights                 │
│  progress_logs │ ai_interaction_logs                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│           FASTAPI BACKEND (Member 2)                │
│                                                     │
│  POST /auth/register  GET /auth/me                  │
│  GET  /foods          GET /foods/{id}               │
│  GET  /recipes        GET /recipes/{id}             │
│  POST /meal-plans     GET /meal-plans/{user_id}     │
│  POST /feedback       GET /progress/{user_id}       │
│         ↓                                           │
│  ┌─────────────────────────────────────┐            │
│  │      HARD SAFETY GATE              │            │
│  │  (Executed BEFORE scoring)         │            │
│  │  • Filter allergens                │            │
│  │  • Enforce dietary restrictions    │            │
│  │  • Validate calorie bounds         │            │
│  └─────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│        HYBRID RECOMMENDATION ENGINE (Member 3)      │
│                                                     │
│  score = (                                          │
│    0.30 × macro_match_score      +                  │
│    0.20 × goal_alignment_score   +                  │
│    0.20 × user_pref_score        +                  │
│    0.15 × feedback_history_score +                  │
│    0.10 × diversity_score        +                  │
│    0.05 × prep_complexity_score                     │
│  )                                                  │
│                                                     │
│  Scikit-learn: Ridge Regression for preference      │
│  weights, KMeans for food clustering, Precision@K   │
│  and NDCG for offline evaluation.                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│        EXPLAINABILITY LAYER (Member 3)              │
│                                                     │
│  SHAP LinearExplainer → feature contribution scores │
│  Deterministic rules → human-readable prose:        │
│  "High in protein (+18%) to meet your muscle goal"  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         GEMINI API INTERFACE (Member 3)             │
│                                                     │
│  System prompt: structured JSON context (facts      │
│  from DB only, never hallucinated).                 │
│  Output: recipe instructions, conversational        │
│  explanation, dietary counselling chat.             │
│                                                     │
│  CONSTRAINT: LLM receives pre-computed facts.       │
│  It NEVER overrides calorie/macro numbers.          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         USER FEEDBACK LOOP (Members 2 & 3)          │
│                                                     │
│  Post-meal rating (1-5) + free-text comment         │
│  → Updates preference_weights table                 │
│  → Re-trains Ridge Regression weights               │
│  → Next recommendation uses updated scores          │
└─────────────────────────────────────────────────────┘
```

---

## 3. Database Entity Relationship (ER Overview)

```
users (1) ──────────────────────── (many) meal_plans
  │                                          │
  │                                          └── (many) meal_plan_items ──── (1) recipes
  ├── (many) dietary_restrictions                                                │
  ├── (1) preference_weights              recipes (1) ──── (many) recipe_ingredients ──── (1) foods
  ├── (many) progress_logs
  ├── (many) user_feedback
  └── (many) ai_interaction_logs
```

### Table Descriptions

| Table | Description |
|-------|-------------|
| `users` | User profile: name, email, age, gender, height, weight, goal (lose/maintain/gain), activity level |
| `dietary_restrictions` | Per-user flags: vegetarian, vegan, gluten-free, allergens (nuts, dairy, shellfish, etc.) |
| `foods` | Raw food items from USDA/ICMR-NIN: name, source, calories, protein, carbs, fat, fiber, sodium, vitamins, minerals (per 100g) |
| `recipes` | Composite meals: name, cuisine type, meal type (breakfast/lunch/dinner/snack), prep_time_mins, serving_size, aggregated macros |
| `recipe_ingredients` | Junction: recipe_id, food_id, quantity_grams |
| `meal_plans` | A daily plan for a user: user_id, date, total_calories_target, total_calories_actual, plan_status |
| `meal_plan_items` | Individual meal slots: meal_plan_id, recipe_id, meal_type, serving_multiplier, score_breakdown (JSONB) |
| `user_feedback` | Post-meal rating: meal_plan_item_id, user_id, rating (1-5), liked_aspects, disliked_aspects, notes |
| `preference_weights` | Per-user adaptive weight vector (JSONB): cuisine preferences, ingredient preferences, disliked ingredients |
| `progress_logs` | Daily: user_id, date, weight_kg, calories_consumed, calories_target, adherence_score |
| `ai_interaction_logs` | Audit trail: user_id, timestamp, prompt_context (JSONB), gemini_response, token_count |

---

## 4. API Contract (Summary)

All endpoints require `Authorization: Bearer <JWT>` except `/auth/register` and `/auth/login`.

```
POST   /auth/register          → Register new user
POST   /auth/login             → Login, returns JWT
GET    /auth/me                → Current user profile

GET    /foods                  → List foods (paginated, filterable)
GET    /foods/{food_id}        → Single food item with full macros
GET    /foods/search?q=...     → Text search on food name

GET    /recipes                → List recipes (filterable by meal_type, cuisine)
GET    /recipes/{recipe_id}    → Single recipe with ingredients + macros
POST   /recipes                → Create new recipe (Data Lead only)

POST   /meal-plans             → Generate a new meal plan for user+date
GET    /meal-plans/{user_id}   → List user's meal plans
GET    /meal-plans/{id}/detail → Full plan with items + SHAP explanations

POST   /feedback               → Submit post-meal rating
GET    /feedback/{user_id}     → Get user's feedback history

GET    /progress/{user_id}     → Weight and calorie trend data
POST   /progress               → Log daily progress entry
```

---

## 5. Scoring Formula Detail

```python
# ml/scoring/formula.py

WEIGHT_MACRO     = 0.30  # How well macros match the user's daily targets
WEIGHT_GOAL      = 0.20  # Alignment with user's weight goal (lose/maintain/gain)
WEIGHT_PREF      = 0.20  # Learned cuisine/ingredient preferences (Ridge Regression)
WEIGHT_FEEDBACK  = 0.15  # Historical rating from similar past meals
WEIGHT_DIVERSITY = 0.10  # Penalize repeating same recipes in recent N days
WEIGHT_PREP      = 0.05  # Prefer simpler prep on weekdays (from user setting)

def compute_score(macro, goal, pref, feedback, diversity, prep) -> float:
    return (
        WEIGHT_MACRO     * macro     +
        WEIGHT_GOAL      * goal      +
        WEIGHT_PREF      * pref      +
        WEIGHT_FEEDBACK  * feedback  +
        WEIGHT_DIVERSITY * diversity +
        WEIGHT_PREP      * prep
    )
```

All sub-scores are normalized to [0, 1] before combining.

---

## 6. Safety Gate Logic

Executed as a database-level filter before any ML scoring:

```sql
-- Pseudo-logic (implemented in backend/app/core/safety_gate.py)
SELECT r.id FROM recipes r
JOIN recipe_ingredients ri ON ri.recipe_id = r.id
JOIN foods f ON f.id = ri.food_id
WHERE r.id NOT IN (
    -- Exclude allergen matches
    SELECT ri2.recipe_id FROM recipe_ingredients ri2
    JOIN foods f2 ON f2.id = ri2.food_id
    WHERE f2.allergen_flags && user_allergen_vector
)
AND r.total_calories BETWEEN :min_cal AND :max_cal
-- Vegetarian/vegan/halal filters applied here
```

---

## 7. Deployment Architecture

```
GitHub (code) → GitHub Actions CI (lint, type-check)
      ↓                    ↓
   Vercel               Render/Railway
  (Next.js)             (FastAPI Docker)
      ↑                    ↓
   Browser          Supabase PostgreSQL
                     (managed, free tier)
```

---

## 8. Environment Variables Reference

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI backend URL |

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only) |
| `JWT_SECRET` | Secret for JWT verification |
| `GEMINI_API_KEY` | Google Gemini API key |
| `ENVIRONMENT` | `development` or `production` |

### ML (`ml/.env`)
| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `DATABASE_URL` | PostgreSQL connection string (read access) |
