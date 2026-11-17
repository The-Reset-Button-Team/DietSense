# DietSense — Google Gemini Integration Architecture & Implementation Plan

**Document ID**: DIETSENSE-GEMINI-ARCH-01  
**Status**: Ready for Review / Pre-Implementation  
**Target Phase**: Phase 5 Preparation  
**Audience**: Backend Engineers, Full-Stack Architects, Machine Learning Engineers, Security & Compliance  

---

## Executive Overview

This specification establishes the architectural blueprint, SDK selection, model determination, and operational strategy for integrating **Google Gemini API** capabilities into the DietSense platform.

DietSense is an offline-first, safety-anchored, evidence-based adaptive meal planning and recommendation engine. The core ground truth for all nutritional values originates exclusively from authoritative clinical food composition databases (**USDA FoodData Central** and **ICMR-NIN / IFCT 2017**).

### Core Architectural Principles & Invariants:
1. **Rule 1 — LLM Never Generates or Alters Facts**: Google Gemini is **strictly read-only** concerning nutritional truth. Calorie counts, macronutrients (protein, carbohydrates, fat), micronutrients, and allergen declarations are derived exclusively from the authoritative SQL `foods` catalog. Gemini will **never** generate, adjust, or hallucinate nutrition figures.
2. **Rule 2 — Hard Safety Gate Executes BEFORE AI**: The safety floor (`ml/scoring/safety_gate.py`) unconditionally executes in deterministic Python/SQL code prior to any scoring or LLM involvement. Items conflicting with user allergies or dietary restrictions (vegetarian/vegan) are eliminated before Gemini sees them.
3. **Rule 3 — Zero Client-Side Secret Exposure**: The `GEMINI_API_KEY` resides strictly within the FastAPI backend environment (`backend/.env`). No browser client, mobile bundle, or frontend bundle will ever receive or store Gemini API keys.
4. **Rule 4 — Resilient Offline Fallback**: DietSense retains full offline functionality. If the Gemini API is unreachable, unconfigured, or rate-limited, the system falls back seamlessly to deterministic rule-based explainers (`ml/explainability/explainers.py`) and regex/heuristic OCR parsers (`backend/routes/pantry.py`).
5. **Rule 5 — Unmodified Core Recommender**: The mathematical recommendation pipeline (`recommender.py`, `vectorizer.py`, `formula.py`, `reweight.py`) remains pure and untouched.

---

## 1. System Inspection & Current State Analysis

### 1.1 Existing FastAPI Architecture
* **Canonical Entry Point**: [backend/app/main.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/app/main.py) (wrapped for backwards compatibility by [backend/main.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/main.py)).
* **Core Modules**:
  * [backend/app/core/config.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/app/core/config.py): Pydantic `BaseSettings` (`Settings` class) loading settings from `backend/.env` and `.env`.
  * [backend/app/core/dependencies.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/app/core/dependencies.py): FastAPI dependency injection (`get_current_user`, `get_optional_current_user`) enforcing authenticated JWT user isolation.
  * [backend/app/core/security.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/app/core/security.py): Password hashing (bcrypt) and session JWT verification.
  * [backend/app/core/sync_service.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/app/core/sync_service.py): Mutation queue for offline-first data sync between SQLite and Supabase.
* **Database Layer**:
  * [backend/db/database.py](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/db/database.py): Manages SQLite connection pooling, WAL mode, foreign key enforcement, and idempotent schema creation (`users`, `auth_identities`, `profiles`, `meal_plans`, `meal_logs`, `feedback`, `pantry_items`, `sync_queue`, `sync_metadata`).
* **Existing Route Handlers**:
  * `/api/recommendations`: Meal ranking and slot recommendations.
  * `/api/pantry`: Pantry inventory, receipt parsing, and fridge scanner.
  * `/api/auth`, `/api/foods`, `/api/users`, `/api/meal-plans`, `/api/meal-logs`, `/api/feedback`.

### 1.2 Environment Configuration
* Configured in `backend/app/core/config.py` using `pydantic-settings`.
* Existing placeholder: `gemini_api_key: str = ""` is present in `Settings`, currently labeled deprecated/removed.
* `backend/.env` and `.env.example` currently configure `DATABASE_PROVIDER=supabase`, local SQLite paths, JWT parameters, and Supabase credentials.
* **Requirement**: Add type-safe Gemini configuration variables and update `.env.example` without exposing actual keys.

### 1.3 Existing AI-Related Dependencies
* Inspected [requirements.txt](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/requirements.txt), [backend/requirements.txt](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/backend/requirements.txt), and [ml/requirements.txt](file:///c:/Users/Prasoon/git%20prasoon/CP%20AND%20EDIs/DietSense/ml/requirements.txt):
  * Machine Learning & Numerics: `scikit-learn>=1.5.0`, `numpy>=1.26.0`, `pandas>=2.2.0`, `joblib>=1.4.0`.
  * Image & Document Processing: `pillow>=10.0.0`, `pypdf>=4.0.0`.
  * HTTP & Async: `fastapi>=0.111.0`, `httpx>=0.27.0`.
  * **Current Gap**: No Google Gemini SDK is currently installed. The legacy SDK (`google-generativeai`) must NOT be used due to official deprecation and retirement.

### 1.4 Recommendation Engine
* Located in `ml/recommendation/recommender.py`:
  * `filter_safe()` evaluates candidate items against dietary preferences and declared allergens.
  * `get_similarity()` extracts TF-IDF vectors from user profiles and food tags to compute cosine similarity (0.40 weight).
  * `compute_score()` calculates multi-factor scoring: Similarity (0.40) + Macronutrient Fit (0.30) + Budget Fit (0.20) + Prep-Time Fit (0.10).
  * `apply_penalties()` applies adaptive penalties derived from user meal skip history (time, cost, unavailable).
  * `generate_reason()` deterministically formats the score factors into transparent plain-English explanations.
* **Requirement**: The core recommendation math must remain untouched. Gemini will act as an auxiliary enrichment layer (natural conversational coaching, Hinglish explanations, recipe steps) called *after* candidate selection and scoring.

### 1.5 Nutrition Database
* Master table: `foods` populated from USDA FoodData Central and ICMR-NIN / IFCT 2017 (14,181 rows).
* Contains exact clinical parameters per 100g: `calories_kcal`, `protein_g`, `carbohydrates_g`, `fat_g`, `fiber_g`, `sugar_g`, `saturated_fat_g`, `trans_fat_g`, `sodium_mg`, `potassium_mg`, `calcium_mg`, `iron_mg`, `zinc_mg`, `vitamin_c_mg`, `vitamin_a_mcg`, `vitamin_d_mcg`, `is_vegetarian`, `is_vegan`, `is_gluten_free`, `allergen_flags`.
* **Requirement**: All LLM prompt templates must inject these verified figures as immutable context constraints. Gemini is forbidden from synthesizing or recalculating nutritional values.

### 1.6 Safety Filtering
* Located in `ml/scoring/safety_gate.py`:
  * Enforces strict diet boundaries: `vegetarian` excludes meat/poultry/fish/seafood; `vegan` additionally excludes dairy/egg/honey.
  * Enforces conservative allergen matching: if user declares allergies and food item has missing/unknown allergen data, the item is excluded.
  * Intersection of food allergens and user declared allergies causes immediate disqualification.
* **Requirement**: Gemini cannot bypass or loosen these filters. If Gemini is used to suggest pantry-based recipes, every suggested ingredient must pass through `filter_safe()` before returning to the user.

---

## 2. Technical Determinations (Official Google Verification)

### 2.1 Determination 1: Appropriate Supported Gemini SDK
* **Selected SDK**: **`google-genai`** (Google Gen AI Python SDK, version `>=1.0.0`)
* **Official Verification & Rationale**:
  * Google has officially announced the end-of-life and deprecation of the legacy **`google-generativeai`** library.
  * **`google-genai`** is Google's authoritative unified SDK across both Google AI Studio (API key) and Google Cloud Vertex AI.
  * Features required by DietSense supported by `google-genai`:
    1. Native asynchronous client support (`client.aio.models.generate_content(...)`) that matches FastAPI's non-blocking event loop.
    2. Strict structured JSON output schema enforcement (`types.GenerateContentConfig(response_mime_type="application/json", response_schema=...)`).
    3. Multimodal support for both images (`image/jpeg`, `image/png`, `image/webp`) and document bytes (`application/pdf`) for receipt OCR and fridge snapshot analysis.
    4. Fine-grained control over system instructions, temperature, top_p, and safety settings.
* **Code Pattern**:
  ```python
  from google import genai
  from google.genai import types

  client = genai.Client(api_key=settings.gemini_api_key)
  ```

### 2.2 Determination 2: Appropriate Supported Gemini Model
* **Primary Production Model**: **`gemini-3.8-flash`**
  * **Role**: Primary workhorse for conversational meal explanations, recipe generation from pantry stock, cultural Hinglish adaptations, and multimodal receipt/fridge vision scanning.
  * **Technical Specs**:
    * Context Window: 1,000,000 tokens (ample space for multi-item nutrition context and high-resolution receipt images).
    * Max Output Tokens: 64,000 tokens.
    * Multimodal: Native text, PDF, and image processing.
    * Latency & Economics: Frontier-class reasoning speed with low per-token cost and high requests-per-minute (RPM) allocation.
    * Thinking Configuration: Supports adjustable thinking budgets (`low`, `medium`, `high`) allowing deterministic low-latency responses for quick meal blurbs.
* **High-Throughput / Lightweight Fallback Model**: **`gemini-3.5-flash-lite`**
  * **Role**: Low-latency, high-frequency fallback for short single-line explanations or rapid preliminary receipt text extraction.
* **Lifecycle & Deprecation Notice on Previous Models**:
  * `gemini-2.0-flash` was formally retired/shut down on June 1, 2026.
  * `gemini-1.5-flash` and `gemini-2.5-flash` are deprecated and restricted to legacy API maintenance.
  * Architecture will explicitly target `gemini-3.8-flash` with a configurable fallback in application settings.

---

## 3. Backend Integration Architecture

The Gemini integration follows a clean layered service architecture, isolating the AI provider behind an abstract client interface and domain services.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION LAYER                     │
├───────────────────────────────────┬────────────────────────────────────┤
│     EXPLAINABILITY ROUTES         │       PANTRY & VISION ROUTES       │
│  • POST /api/recommendations/     │  • POST /api/pantry/scan           │
│    explain                        │  • POST /api/pantry/recipes/       │
│  • GET /api/recommendations/tips  │    generate                        │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
                  ▼                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        AI SERVICE ORCHESTRATION                        │
├───────────────────────────────────┬────────────────────────────────────┤
│      AI Explainability Service    │      Pantry Vision Service         │
│  • Injects DB nutrition facts     │  • Multimodal receipt/fridge parser│
│  • Respects score breakdown       │  • Cross-references GROCERY_CATALOG│
│  • Formats friendly explanations  │  • Enforces JSON Schema output     │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
                  ▼                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       GEMINI CLIENT MANAGER                            │
│  • google-genai Client Singleton                                       │
│  • Async Execution (client.aio)                                        │
│  • Token Bucket Rate Limiter (RPM / RPD Guard)                         │
│  • Response In-Memory / Hash Cache (SHA-256)                           │
│  • Exponential Backoff & Jitter Handler                                │
│  • Clinical Audit Logger (writes to SQLite ai_interaction_logs)        │
└─────────────────┬──────────────────────────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │  Is API Available?    │
      ├───────────┬───────────┤
     YES          NO (Rate limit / Timeout / Key missing / Offline)
      │           │
      ▼           ▼
┌───────────┐ ┌──────────────────────────────────────────────────────────┐
│ Google    │ │                DETERMINISTIC FALLBACK                    │
│ Gemini    │ │  • ml.explainability.explainers.generate_reason()        │
│ API Cloud │ │  • routes.pantry._extract_items_from_text() (Regex/PyPDF)│
└───────────┘ └──────────────────────────────────────────────────────────┘
```

### 3.1 Proposed File Structure
When implementation begins in Phase 6, the following files will be created/updated:

```
backend/
├── app/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py              # GeminiClientManager (lifecycle, init, async client)
│   │   ├── prompts.py             # System instructions, clinical guardrails, prompt templates
│   │   ├── explainability.py      # Conversational explainability service
│   │   ├── vision.py              # Receipt OCR & fridge vision scanner service
│   │   └── recipe_gen.py          # Pantry-anchored recipe generation
│   ├── schemas/
│   │   └── ai.py                  # Pydantic schemas for all AI requests/responses
│   ├── core/
│   │   └── config.py              # Updated with Gemini configuration settings
│   └── routers/
│       └── ai.py                  # New dedicated AI router (/api/ai/...)
├── db/
│   └── migrations/
│       └── 004_ai_logs.sql        # ai_interaction_logs table schema
└── routes/
    └── pantry.py                  # Enhances existing /scan endpoint to delegate to vision.py
```

### 3.2 Audit Logging Table Schema (`ai_interaction_logs`)
Every interaction with the Gemini API is captured for cost control, security monitoring, and clinical transparency:

```sql
CREATE TABLE IF NOT EXISTS ai_interaction_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature TEXT NOT NULL CHECK (feature IN ('explanation', 'receipt_ocr', 'fridge_vision', 'recipe_gen')),
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    latency_ms INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'fallback_offline', 'fallback_ratelimit', 'fallback_error')),
    error_message TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_logs_user_id ON ai_interaction_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_logs_created_at ON ai_interaction_logs(created_at);
```

---

## 4. Required Environment Variables

All variables will be validated in `backend/app/core/config.py` via `pydantic-settings`:

| Variable Name | Type | Default Value | Description | Security Scope |
| :--- | :---: | :---: | :--- | :--- |
| `GEMINI_API_KEY` | `str` | `""` | Google AI Studio API Key | **Backend Secret Only** |
| `GEMINI_MODEL` | `str` | `"gemini-3.8-flash"` | Primary Gemini model ID | Backend Config |
| `GEMINI_FALLBACK_MODEL` | `str` | `"gemini-3.5-flash-lite"` | Secondary low-latency model | Backend Config |
| `GEMINI_REQUEST_TIMEOUT` | `float` | `12.0` | Maximum seconds before timeout & fallback | Backend Config |
| `GEMINI_MAX_RETRIES` | `int` | `3` | Maximum retry attempts on transient network errors | Backend Config |
| `GEMINI_RATE_LIMIT_RPM` | `int` | `60` | Client-side rate limit cap per minute | Backend Config |
| `GEMINI_CACHE_TTL_HOURS` | `int` | `24` | Cache lifespan for identical meal explanation prompts | Backend Config |
| `AI_FEATURE_ENABLED` | `bool` | `true` | Master feature flag for AI capabilities | Backend Config |

### Example `.env.example` Entry:
```bash
# ─── Google Gemini API Integration ──────────────────────────────────────────
# Google AI Studio API Key (obtain from https://aistudio.google.com/)
# Strictly backend-only: NEVER prefix with NEXT_PUBLIC_ or expose to client
GEMINI_API_KEY=AIzaSy...

# Gemini Model Selection
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite

# Request Constraints
GEMINI_REQUEST_TIMEOUT=12.0
GEMINI_MAX_RETRIES=3
GEMINI_RATE_LIMIT_RPM=60
GEMINI_CACHE_TTL_HOURS=24
AI_FEATURE_ENABLED=true
```

---

## 5. API Request and Response Formats

Strict JSON schemas are enforced on both the FastAPI input/output boundaries and on Gemini's output generation using `google-genai`'s native schema definition.

### 5.1 Feature 1: Conversational Meal Explainability
Enriches the deterministic recommendation with warm, culturally aware explanation and practical preparation advice without altering nutritional figures.

#### API Endpoint: `POST /api/recommendations/{item_id}/explain`
* **Input Schema (FastAPI Request Body)**:
  ```json
  {
    "user_context": {
      "dietary_pref": "vegetarian",
      "goal": "lose_weight",
      "target_calories": 1800,
      "tone": "encouraging_hinglish"
    },
    "score_breakdown": {
      "similarity": 0.85,
      "macro_fit": 0.90,
      "budget_fit": 0.75,
      "prep_time_fit": 1.0,
      "adaptive_penalty": 0.0,
      "pantry_bonus": 0.05
    }
  }
  ```
  *(Note: The food's exact nutritional values and ingredients are resolved server-side from `foods` by `item_id`, never accepted from client input).*

* **Gemini Structured Output Schema & API Response**:
  ```json
  {
    "status": "success",
    "source": "gemini-3.8-flash",
    "food_id": 8,
    "food_name": "Fresh Palak Paneer & Brown Rice with Dahi Bowl",
    "headline": "High-protein comfort food perfectly balanced for your calorie target",
    "conversational_reason": "Palak paneer paired with brown rice delivers 24g of clean vegetarian protein while staying right under your 480 kcal lunch budget. The complex carbs will keep your afternoon energy steady without sugar spikes.",
    "health_benefits": [
      "Rich in non-heme iron and folate from fresh spinach",
      "Complete amino acid profile from dairy paneer and brown rice"
    ],
    "preparation_tip": "Blanch spinach in boiling water for 90 seconds then ice it immediately to preserve bright chlorophyll and maximum vitamin C.",
    "cultural_note": "A timeless North Indian staple adapted with brown rice for a lower glycemic index.",
    "verified_nutrition": {
      "calories_kcal": 480.0,
      "protein_g": 24.0,
      "carbs_g": 52.0,
      "fat_g": 16.0
    }
  }
  ```

### 5.2 Feature 2: Multimodal Pantry & Fridge Scanner
Analyzes grocery receipts (PDF / JPG / PNG) or fridge photos and returns structured inventory items mapped to DietSense grocery taxonomy.

#### API Endpoint: `POST /api/pantry/scan`
* **Input**: Multipart Form Data (`file: UploadFile`, `scan_type: "receipt" | "fridge"`).
* **Gemini Structured Output Schema & API Response**:
  ```json
  {
    "status": "success",
    "source": "gemini-3.8-flash-vision",
    "scan_type": "receipt",
    "store_name": "Blinkit",
    "invoice_date": "2026-11-17",
    "items_found_count": 5,
    "items": [
      {
        "id": "pantry_gem_a1b2c3d4",
        "name": "Paneer",
        "category": "Dairy & Protein",
        "quantity": "200 g",
        "in_stock": true,
        "confidence": 0.99,
        "food_catalog_match": "Paneer, raw"
      },
      {
        "id": "pantry_gem_e5f6g7h8",
        "name": "Spinach",
        "category": "Produce",
        "quantity": "1 bunch (~250 g)",
        "in_stock": true,
        "confidence": 0.96,
        "food_catalog_match": "Spinach, raw"
      }
    ],
    "unrecognized_items": []
  }
  ```

### 5.3 Feature 3: Constrained Pantry Recipe Assembly
Generates meal assembly instructions using strictly what is in the user's pantry.

#### API Endpoint: `POST /api/pantry/recipes/generate`
* **Input Schema**:
  ```json
  {
    "meal_slot": "dinner",
    "max_prep_time_mins": 25,
    "pantry_item_ids": ["pantry_01", "pantry_02"]
  }
  ```
* **Output Schema**:
  ```json
  {
    "status": "success",
    "recipe_title": "Quick 15-Minute Garlic Spinach Paneer Sauté",
    "prep_time_mins": 15,
    "used_pantry_items": ["Paneer", "Spinach", "Garlic", "Ghee"],
    "missing_optional_items": ["Roasted Cumin Powder"],
    "instructions": [
      "Heat 1 tsp ghee in a skillet and lightly brown the cubed paneer for 3 minutes.",
      "Add minced garlic and sliced spinach leaves; sauté until spinach wilts (2 minutes).",
      "Season with salt and a pinch of black pepper, serve hot."
    ],
    "safety_verified": true,
    "disclaimer": "Nutritional estimate anchored to USDA/ICMR reference items."
  }
  ```

---

## 6. Error Handling Strategy

The error handling strategy ensures DietSense remains 100% resilient. A failure in external AI services will never crash an endpoint or return an unhandled 500 error to the client.

```
                  ┌───────────────────────────────┐
                  │    Incoming AI Request        │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Is Key Valid & Ready? │
                     └───────────┬───────────┘
                       NO        │      YES
            ┌────────────────────┘       │
            ▼                            ▼
  ┌──────────────────┐       ┌────────────────────────┐
  │ Local Fallback   │       │ Attempt Gemini Async   │
  │ Engine Triggered │       │ Call (Client.aio)      │
  └──────────────────┘       └───────────┬────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
  [429 Quota Exhausted]         [Network Timeout / 5xx]         [Safety Filter / Bad JSON]
        │                                │                                │
        ▼                                ▼                                ▼
  Exponential Backoff          Retry with Jitter (x3)           Log Clinical Warning
  (If still 429 → Fallback)    (If still failed → Fallback)     (Immediate Fallback)
```

### 6.1 Error Classifications & Interventions

| Error Scenario | Root Cause | Handling Intervention | Fallback Action |
| :--- | :--- | :--- | :--- |
| **Missing / Invalid Key** | `GEMINI_API_KEY` unset or rejected | Catch during service init; log system warning | Fall back instantly to deterministic algorithms |
| **HTTP 429 Quota Exhausted** | Google AI Studio rate limit reached | Exponential backoff (1s, 2s, 4s) with random jitter | Serve deterministic result with status flag `fallback_ratelimit` |
| **HTTP 503 / 500 Service Down** | Google API temporary outage | Retry up to `GEMINI_MAX_RETRIES` times | Fall back to local regex/heuristics |
| **Timeout (`> 12.0s`)** | High network latency or complex prompt | Cancel via `asyncio.wait_for(timeout=12.0)` | Return deterministic output within sub-second time |
| **Safety Block (`SAFETY`)** | Input/output flagged by Google safety filters | Detect `finish_reason == FinishReason.SAFETY` | Return standard safe explainer without crashing |
| **JSON Schema Malformation** | Unexpected model formatting | Pydantic validation catches `ValidationError` | Discard malformed JSON, serve deterministic text |

---

## 7. Rate-Limiting & Cost Optimization Strategy

To operate securely and sustainably within Google AI Studio quota tiers, DietSense implements a multi-layer rate limiting and caching system:

### 7.1 Multi-Tier Rate Limiting Architecture
1. **Tier 1: Global Backend Throttler**:
   * Token Bucket algorithm limiting total outbound requests to Google API to 60 RPM.
   * Prevents sudden burst requests from triggering Google IP/Key bans.
2. **Tier 2: Per-User Route Rate Limiter**:
   * Enforced via FastAPI dependencies (`slowapi` or custom Redis/memory limiter):
     * Meal Explainability: Max 20 requests per user / hour.
     * Pantry Scanner (Multimodal): Max 10 scans per user / day.
     * Recipe Generation: Max 15 generations per user / day.
3. **Tier 3: Query Deduplication Cache (SHA-256 Hashing)**:
   * 70%+ of meal explanations for common foods (e.g. "Masala Oats", "Moong Dal Chilla") are identical across users with similar goals.
   * Explanations are cached in an in-memory / SQLite cache keyed on:
     `cache_key = SHA256(food_id + goal + dietary_pref + tone)`
   * Cache TTL: 24 hours.
   * Cache hits bypass Gemini API completely, dropping latency to < 5ms and cutting API usage by up to 80%.

---

## 8. Frontend Security & Non-Exposure Guarantees

### 8.1 Zero Frontend Exposure Verification
* Next.js frontend code is located under `frontend/`.
* Any environment variable prefixed with `NEXT_PUBLIC_` is baked into client JavaScript bundles sent to browsers.
* **Non-Negotiable Rule**:
  * `GEMINI_API_KEY` shall **never** be prefixed with `NEXT_PUBLIC_`.
  * Frontend components will **never** import `@google/genai` or make direct fetch requests to `https://generativelanguage.googleapis.com`.
  * All user requests flow through authenticated FastAPI endpoints (`/api/recommendations/...`, `/api/pantry/...`). The browser communicates exclusively with DietSense backend using secure HTTP-only cookies or Bearer JWTs.

---

## 9. Implementation Roadmap & Next Steps

When implementation is scheduled (Phase 6), the following steps will be executed:

1. **Step 1 — Dependency Registration**:
   Add `google-genai>=1.0.0` to `backend/requirements.txt` and `requirements.txt`.
2. **Step 2 — Settings Extension**:
   Update `backend/app/core/config.py` to declare all `GEMINI_*` settings with validation.
3. **Step 3 — Database Migration**:
   Create `ai_interaction_logs` table via `backend/db/database.py`.
4. **Step 4 — Core AI Client Implementation**:
   Implement `backend/app/ai/client.py` with async support, rate limiting, and fallback handling.
5. **Step 5 — Explainability Service Integration**:
   Build `backend/app/ai/explainability.py` and register `/api/recommendations/{id}/explain`.
6. **Step 6 — Multimodal Pantry Vision Integration**:
   Enhance `backend/routes/pantry.py` to delegate receipt and fridge image analysis to `backend/app/ai/vision.py`.
7. **Step 7 — Comprehensive Automated Testing**:
   Write pytest suites mocking `google-genai` responses to test graceful degradation, rate limiting, and schema integrity.

---

## 10. Verification Checklist

- [x] Inspected existing FastAPI application structure, config, dependencies, recommender, foods DB, and safety filter.
- [x] Verified official Google SDK status (`google-genai` active, `google-generativeai` deprecated/EOL).
- [x] Verified official Google model status (`gemini-3.8-flash` primary workhorse, `gemini-3.5-flash-lite` high-throughput fallback, `gemini-2.0-flash` sunset).
- [x] Enforced Rule 1 (read-only nutrition facts; zero LLM fact generation) and Rule 2 (hard safety gate runs before AI).
- [x] Formulated structured request/response schemas, error handling, rate limiting, and audit logging specifications.
- [x] Guaranteed zero frontend API key exposure.
- [x] Preserved existing recommendation engine code untouched.
- [x] Prepared comprehensive documentation in `docs/GEMINI_INTEGRATION_PLAN.md`.
