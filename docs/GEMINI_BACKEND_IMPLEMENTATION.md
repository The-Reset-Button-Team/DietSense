# DietSense — Gemini Backend Implementation & Operations Guide

**Document ID**: DIETSENSE-GEMINI-IMPL-01  
**Status**: Implemented & Verified (93/93 Tests Passing)  
**Target Phase**: Phase 6 Completion  
**Audience**: Backend Engineers, QA Engineers, Security & Operations  

---

## 1. Executive Summary

Phase 6 implements Google Gemini generative AI features within the DietSense FastAPI backend, anchored to verified clinical nutrition data.

All interactions adhere strictly to DietSense core architecture:
1. **Rule 1 — Nutrition Ground Truth**: Caloric and macronutrient numbers originate exclusively from the authoritative SQL `foods` catalog (14,181 clinical records from USDA FoodData Central and ICMR-NIN / IFCT 2017). Gemini is **never** permitted to fabricate or alter nutrition facts.
2. **Rule 2 — Hard Safety Gate Priority**: The deterministic safety floor (`ml/scoring/safety_gate.py`) executes before any recipe or meal is presented, strictly enforcing vegetarian, vegan, and allergen declarations.
3. **Rule 3 — Non-Diagnostic Medical Boundary**: DietSense does not provide medical diagnoses or disease treatments. Every AI response includes a standardized medical disclaimer.
4. **Rule 4 — Resilient Offline Fallback**: In the absence of an API key, during network timeouts, or upon Google API rate-limiting, the backend transparently returns deterministic rule-based responses without errors.
5. **Rule 5 — Zero Frontend Secret Exposure**: The `GEMINI_API_KEY` remains strictly confidential inside `backend/.env`. All client interactions route through authenticated FastAPI proxy endpoints.

---

## 2. Implemented Architecture & Module Structure

The Gemini implementation is organized in `backend/app/ai/`:

```
backend/app/
├── ai/
│   ├── __init__.py            # Service and client exports
│   ├── client.py              # GeminiClientManager (async execution, audit logging, timeouts)
│   ├── rate_limiter.py        # Sliding window rate limiter & SHA-256 TTL response cache
│   ├── prompts.py             # Grounded system instructions & structured prompt templates
│   ├── fallback.py           # 100% deterministic offline fallback engine
│   └── service.py             # GeminiService facade (DB retrieval, safety filtering, fallbacks)
├── routers/
│   └── ai.py                  # FastAPI router mounted at /api/ai
├── schemas/
│   └── ai.py                  # Pydantic v2 schemas for all requests and responses
└── core/
    └── config.py              # Type-safe Gemini configuration parameters
```

---

## 3. Endpoints Implemented

All endpoints are mounted under `/api/ai`:

### 3.1 AI Meal Assistant
* **Route**: `POST /api/ai/assistant`
* **Purpose**: Conversational nutrition assistant answering questions regarding meal timing, calorie targets, and dietary balances.
* **Grounding**: Automatically resolves user profile and active foods catalog candidates, injecting verified nutrition into the prompt.
* **Request**:
  ```json
  {
    "query": "What is a good high-protein snack for the evening?",
    "context_food_ids": [1, 2],
    "meal_slot": "evening_snack"
  }
  ```
* **Response**:
  ```json
  {
    "reply": "Moong Dal Chilla or roasted makhana are great options providing slow-release protein without glycemic spikes.",
    "suggested_foods": [...],
    "source": "gemini-3.8-flash",
    "disclaimer": "DietSense provides evidence-based nutritional guidance and does not provide medical diagnoses..."
  }
  ```

### 3.2 Meal Recommendation Explanation
* **Route**: `POST /api/ai/recommendations/{food_id}/explain`
* **Purpose**: Generates a warm, personalized explanation of why a candidate was ranked highly by the ML scoring engine.
* **Grounding**: Queries exact calories, protein, carbs, fat, and allergen flags from `foods` by `food_id`. Passes the real ML score breakdown (similarity, macro fit, budget fit, prep time fit).
* **Response**:
  ```json
  {
    "food_id": 2,
    "food_name": "Moong Dal & Oats Chilla",
    "headline": "High-protein comfort food perfectly balanced for your calorie target",
    "explanation": "Provides steady slow-burn energy and 18g protein for your fitness goals...",
    "key_benefits": [
      "Rich in dietary fiber",
      "Supports muscle protein synthesis"
    ],
    "preparation_tip": "Cook on medium heat with minimal ghee for a crispy texture.",
    "verified_nutrition": {
      "calories_kcal": 380.0,
      "protein_g": 18.0,
      "carbohydrates_g": 48.0,
      "fat_g": 7.0
    },
    "source": "gemini-3.8-flash"
  }
  ```

### 3.3 Recipe Suggestions
* **Route**: `POST /api/ai/recipes/suggest`
* **Purpose**: Recommends balanced recipe concepts matching a meal slot and calorie budget.
* **Safety Invariant**: Candidate pool is pre-filtered by `filter_safe()` so allergens and non-veg items are strictly excluded.
* **Response**:
  ```json
  {
    "suggestions": [
      {
        "title": "Zesty Spiced Dal Tadka",
        "meal_slot": "lunch",
        "estimated_prep_time_mins": 20,
        "matched_catalog_food_id": 3,
        "ingredients": ["1 cup Yellow Dal", "1 Tomato", "1 tsp Jeera"],
        "overview": "Comforting protein-rich dal with warming Indian spices.",
        "verified_nutrition_estimate": {
          "calories_kcal": 380,
          "protein_g": 16,
          "carbs_g": 52,
          "fat_g": 6
        }
      }
    ],
    "source": "gemini-3.8-flash"
  }
  ```

### 3.4 Pantry-Based Cooking Assistant
* **Route**: `POST /api/ai/pantry/cook`
* **Purpose**: Synthesizes quick, low-waste home meals utilizing in-stock ingredients detected from grocery receipts or user pantry records.
* **Grounding**: Cross-references user pantry items with catalog candidates to derive realistic prep steps and macro estimates.
* **Response**:
  ```json
  {
    "recipes": [
      {
        "recipe_name": "Quick Kadai Paneer Toss",
        "prep_time_mins": 15,
        "matched_pantry_items": ["Paneer", "Tomato"],
        "missing_items": ["Kasuri Methi"],
        "cooking_steps": ["Cube paneer", "Toss in tomato puree with cumin", "Simmer 5 mins"],
        "nutrition_anchor_food_id": 7,
        "nutrition_anchor_name": "Paneer",
        "nutrition_facts": {"calories_kcal": 320, "protein_g": 18, "carbs_g": 10, "fat_g": 22}
      }
    ],
    "available_pantry_items": ["Paneer", "Tomato", "Spinach"],
    "pantry_matched_count": 3,
    "source": "gemini-3.8-flash"
  }
  ```

### 3.5 Meal Comparison
* **Route**: `POST /api/ai/compare`
* **Purpose**: Compares 2 to 5 foods objectively side-by-side.
* **Grounding**: Queries exact clinical values for each food ID from SQLite. Evaluates highest protein, lowest calorie density, and cost trade-offs.
* **Validation**: Enforces `min_length=2, max_length=5` on `food_ids`.
* **Response**:
  ```json
  {
    "compared_meals": [...],
    "analysis": "Meal 2 provides double the protein with identical prep time.",
    "key_tradeoffs": ["Moong Dal Chilla has 18g protein vs Poha 8.5g", "Poha is marginally lighter in fat"],
    "winner_for_goal": "Moong Dal & Oats Chilla",
    "macro_comparison": {
      "highest_protein": "Moong Dal & Oats Chilla",
      "lowest_calorie": "Vegetable Poha with Peanuts"
    },
    "source": "gemini-3.8-flash"
  }
  ```

### 3.6 Cooking Instructions
* **Route**: `POST /api/ai/recipes/{food_id}/instructions`
* **Purpose**: Generates beginner-friendly, step-by-step cooking instructions with scaled ingredient quantities and healthy chef tips (e.g. low-sodium techniques).
* **Grounding**: Quantities and nutrition scale proportionally with the `servings` parameter.

---

## 4. Engineering Guardrails & Reliability Controls

### 4.1 Rate Limiting (`RateLimiter`)
* Implemented in `backend/app/ai/rate_limiter.py` using a thread-safe sliding window algorithm.
* **Limits Enforced**:
  * Global Outbound Limit: 60 requests per minute.
  * User-Level Limit: 30 requests per minute per authenticated user or IP.
* When limits are exceeded, the request does not fail; it triggers the deterministic fallback with status `fallback_ratelimit`.

### 4.2 Hashed Deduplication Cache (`ResponseCache`)
* Implemented in `backend/app/ai/rate_limiter.py`.
* Caches identical requests using deterministic SHA-256 hashes:
  `cache_key = SHA256(feature + food_id + goal + dietary_pref + tone)`
* TTL: 24 hours (86,400 seconds).
* Drastically reduces token costs and latency for frequently recommended meals.

### 4.3 Timeout Enforcement
* Gemini async calls are wrapped with `asyncio.wait_for(..., timeout=settings.gemini_request_timeout)` (default: 12.0s).
* If Google API takes longer than 12 seconds, execution cancels and the deterministic fallback is served in < 5ms.

### 4.4 Clinical Audit Logging (`ai_interaction_logs`)
* Every AI invocation records an entry into SQLite table `ai_interaction_logs`:
  * `id`: Unique log identifier (`ai_log_*`).
  * `user_id`: Authenticated user ID (or `"anonymous"`).
  * `feature`: Feature category (`assistant`, `explain`, `recipe_suggest`, `pantry_cook`, `compare`, `cooking_instructions`).
  * `model`: Model identifier (`gemini-3.8-flash`).
  * `prompt_tokens`, `completion_tokens`, `total_tokens`.
  * `latency_ms`: Duration of the API call.
  * `status`: `success`, `cached`, `fallback_offline`, `fallback_timeout`, `fallback_error`, `fallback_ratelimit`.
  * `created_at`: UTC timestamp.
* No raw passwords or sensitive credentials are ever logged.

### 4.5 Fallback Engine (`backend/app/ai/fallback.py`)
* Dedicated deterministic implementations for all 6 operations.
* Integrates `ml.explainability.explainers.generate_reason` for continuous consistency with the core recommendation pipeline.

---

## 5. Verification & Test Results

Automated test suite in `tests/test_gemini_backend.py` validates all failure modes and mocked Gemini responses:

| Test Case | Scope | Result |
| :--- | :--- | :---: |
| `test_assistant_offline_fallback` | Verifies assistant fallback when unconfigured | PASSED |
| `test_assistant_mocked_gemini_success` | Verifies assistant when Gemini succeeds | PASSED |
| `test_assistant_input_validation` | Verifies rejection of too-short queries (422) | PASSED |
| `test_explain_recommendation_offline_fallback` | Verifies explanation fallback with verified nutrition | PASSED |
| `test_explain_recommendation_mocked_gemini` | Verifies structured JSON explanation parsing | PASSED |
| `test_recipe_suggestions_offline_fallback` | Verifies safe candidate-based recipe suggestions | PASSED |
| `test_recipe_suggestions_mocked_gemini` | Verifies Gemini structured recipe output | PASSED |
| `test_pantry_cook_offline_fallback` | Verifies home-style recipe generation from pantry | PASSED |
| `test_pantry_cook_mocked_gemini` | Verifies Gemini pantry cooking assistant | PASSED |
| `test_compare_meals_requires_at_least_two_items` | Verifies 422 validation on < 2 food IDs | PASSED |
| `test_compare_meals_offline_fallback` | Verifies mathematical macro comparison | PASSED |
| `test_compare_meals_mocked_gemini` | Verifies Gemini trade-off reasoning | PASSED |
| `test_cooking_instructions_offline_fallback` | Verifies step-by-step instructions fallback | PASSED |
| `test_cooking_instructions_mocked_gemini` | Verifies Gemini culinary step parsing | PASSED |
| `test_api_failure_triggers_graceful_fallback` | Verifies runtime 503 errors trigger fallback (200 OK) | PASSED |
| `test_api_timeout_triggers_graceful_fallback` | Verifies asyncio.TimeoutError triggers fallback | PASSED |
| `test_empty_response_triggers_graceful_fallback` | Verifies empty Gemini response triggers fallback | PASSED |
| `test_rate_limiting_enforcement` | Verifies user rate limit tripping triggers fallback | PASSED |

### Full Test Suite Status:
```
tests/test_auth.py: 7 passed
tests/test_etl.py: 4 passed
tests/test_gemini_backend.py: 18 passed
tests/test_local_auth_db.py: 8 passed
tests/test_meal_workflow.py: 6 passed
tests/test_pantry_scanner.py: 4 passed
tests/test_phase3_supabase_auth.py: 13 passed
tests/test_phase4_sync.py: 7 passed
tests/test_recommendations.py: 4 passed
tests/test_scoring.py: 6 passed
tests/test_slot_recommendations.py: 9 passed
tests/test_supabase_integration.py: 7 passed

Total: 93 PASSED in 86.69s (100% Pass Rate)
```

---

## 6. How to Run & Verify

1. Run the Gemini backend test suite:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_gemini_backend.py -v
   ```

2. Run the complete test suite:
   ```powershell
   .venv\Scripts\pytest.exe tests
   ```

3. Start the FastAPI server locally:
   ```powershell
   $env:PYTHONPATH = ".;backend"
   .venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```
   Interactive Swagger documentation will be available at: `http://localhost:8000/docs`.
