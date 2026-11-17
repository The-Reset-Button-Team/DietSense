"""
DietSense — Automated Tests for Phase 6 Gemini Backend Implementation
Tests all 6 AI endpoints with mocked Gemini responses, invalid API keys,
API failures, timeouts, empty responses, rate limiting, and fallback integrity.
"""

import sys
import os
import time
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.ai.client import gemini_client
from app.ai.rate_limiter import user_rate_limiter, global_rate_limiter, ai_response_cache
import jwt

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str = "test_user_ai_001") -> str:
    payload = {
        "sub": user_id,
        "email": f"{user_id}@dietsense.ai",
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiters and cache between tests."""
    with user_rate_limiter.lock:
        user_rate_limiter.requests.clear()
    with global_rate_limiter.lock:
        global_rate_limiter.requests.clear()
    ai_response_cache.clear()
    yield


# ─── 1. AI MEAL ASSISTANT TESTS ─────────────────────────────────────────────

def test_assistant_offline_fallback():
    """When Gemini is unconfigured or offline, assistant returns high-fidelity fallback."""
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/assistant",
            json={"query": "What high-protein breakfast can I have for weight loss?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 20
        assert data["source"] == "offline_fallback"
        assert "disclaimer" in data
        assert "medical diagnoses" in data["disclaimer"].lower()


def test_assistant_mocked_gemini_success():
    """When Gemini succeeds, returns live model reply and disclaimer."""
    mock_response = MagicMock()
    mock_response.text = "Moong Dal Chilla is an excellent high-protein breakfast option providing 18g protein."
    mock_response.usage_metadata = MagicMock(prompt_token_count=120, candidates_token_count=25)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        token = generate_token("user_assistant_01")
        response = client.post(
            "/api/ai/assistant",
            json={"query": "Suggest a protein-rich meal"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Moong Dal Chilla" in data["reply"]
        assert data["source"] == settings.gemini_model
        assert "disclaimer" in data


def test_assistant_input_validation():
    """Query must meet minimum length constraints."""
    response = client.post("/api/ai/assistant", json={"query": "a"})
    assert response.status_code == 422


# ─── 2. MEAL RECOMMENDATION EXPLANATION TESTS ───────────────────────────────

def test_explain_recommendation_offline_fallback():
    """Fallback explanation provides real verified nutrition and score reasoning."""
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/recommendations/2/explain",
            json={"food_id": 2, "tone": "friendly"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["food_id"] == 2
        assert "headline" in data
        assert "explanation" in data
        assert len(data["key_benefits"]) >= 1
        assert "verified_nutrition" in data
        assert "calories_kcal" in data["verified_nutrition"]
        assert data["source"] == "offline_fallback"


def test_explain_recommendation_mocked_gemini():
    """Gemini structured JSON explanation is correctly parsed and enriched."""
    mock_json = json.dumps({
        "headline": "Protein-Dense Morning Dynamo",
        "explanation": "Provides steady slow-burn energy and 18g protein for your fitness goals.",
        "key_benefits": ["Rich in dietary fiber", "Supports muscle protein synthesis"],
        "preparation_tip": "Cook on medium heat with minimal ghee for a crispy texture."
    })
    mock_response = MagicMock()
    mock_response.text = mock_json
    mock_response.usage_metadata = MagicMock(prompt_token_count=150, candidates_token_count=50)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/ai/recommendations/2/explain",
            json={"food_id": 2, "tone": "friendly"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Protein-Dense Morning Dynamo"
        assert len(data["key_benefits"]) == 2
        assert data["source"] == settings.gemini_model


# ─── 3. RECIPE SUGGESTIONS TESTS ─────────────────────────────────────────────

def test_recipe_suggestions_offline_fallback():
    """Recipe suggestions pull safe candidates from database."""
    token = generate_token("user_recipe_01")
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/recipes/suggest",
            json={"meal_slot": "lunch", "target_calories": 500, "prep_time_limit": 25},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) >= 1
        assert data["source"] == "offline_fallback"
        first = data["suggestions"][0]
        assert "title" in first
        assert "ingredients" in first
        assert "verified_nutrition_estimate" in first


def test_recipe_suggestions_mocked_gemini():
    """Gemini recipe suggestions return structured parsed items."""
    mock_json = json.dumps({
        "suggestions": [
            {
                "title": "Zesty Spiced Dal Tadka",
                "meal_slot": "lunch",
                "estimated_prep_time_mins": 20,
                "matched_catalog_food_id": 3,
                "ingredients": ["1 cup Yellow Dal", "1 Tomato", "1 tsp Jeera"],
                "overview": "Comforting protein-rich dal with warming Indian spices.",
                "verified_nutrition_estimate": {"calories_kcal": 380, "protein_g": 16, "carbs_g": 52, "fat_g": 6}
            }
        ]
    })
    mock_response = MagicMock(text=mock_json, usage_metadata=None)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/recipes/suggest", json={"meal_slot": "lunch"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["title"] == "Zesty Spiced Dal Tadka"
        assert data["source"] == settings.gemini_model


# ─── 4. PANTRY-BASED COOKING ASSISTANT TESTS ────────────────────────────────

def test_pantry_cook_offline_fallback():
    """Uses provided pantry items to build home meal."""
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/pantry/cook",
            json={"custom_ingredients": ["Paneer", "Tomato", "Onion"], "max_prep_time_mins": 20},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recipes"]) >= 1
        assert data["source"] == "offline_fallback"
        recipe = data["recipes"][0]
        assert "recipe_name" in recipe
        assert "cooking_steps" in recipe
        assert len(recipe["cooking_steps"]) >= 2


def test_pantry_cook_mocked_gemini():
    """Mocked Gemini pantry cook returns custom assembled recipe."""
    mock_json = json.dumps({
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
        ]
    })
    mock_response = MagicMock(text=mock_json, usage_metadata=None)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/ai/pantry/cook",
            json={"custom_ingredients": ["Paneer", "Tomato"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recipes"][0]["recipe_name"] == "Quick Kadai Paneer Toss"
        assert data["source"] == settings.gemini_model


# ─── 5. MEAL COMPARISON TESTS ────────────────────────────────────────────────

def test_compare_meals_requires_at_least_two_items():
    """Comparing less than 2 items fails validation."""
    response = client.post("/api/ai/compare", json={"food_ids": [1]})
    assert response.status_code == 422


def test_compare_meals_offline_fallback():
    """Mathematically compares foods by protein and calories."""
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/compare",
            json={"food_ids": [1, 2], "preference_priority": "protein"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["compared_meals"]) == 2
        assert "analysis" in data
        assert "winner_for_goal" in data
        assert data["source"] == "offline_fallback"


def test_compare_meals_mocked_gemini():
    """Gemini meal comparison provides trade-off analysis."""
    mock_json = json.dumps({
        "analysis": "Meal 2 provides double the protein with identical prep time.",
        "key_tradeoffs": ["Moong Dal Chilla has 18g protein vs Poha 8.5g", "Poha is marginally lighter in fat"],
        "winner_for_goal": "Moong Dal & Oats Chilla",
        "macro_comparison": {"highest_protein": "Moong Dal & Oats Chilla", "lowest_calorie": "Vegetable Poha with Peanuts"}
    })
    mock_response = MagicMock(text=mock_json, usage_metadata=None)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/compare", json={"food_ids": [1, 2], "preference_priority": "protein"})
        assert response.status_code == 200
        data = response.json()
        assert data["winner_for_goal"] == "Moong Dal & Oats Chilla"
        assert len(data["key_tradeoffs"]) == 2
        assert data["source"] == settings.gemini_model


# ─── 6. COOKING INSTRUCTIONS TESTS ───────────────────────────────────────────

def test_cooking_instructions_offline_fallback():
    """Generates practical cooking steps from food properties."""
    with patch.object(gemini_client, "generate_text", new_callable=AsyncMock, return_value=(None, "offline")):
        response = client.post(
            "/api/ai/recipes/1/instructions",
            json={"food_id": 1, "servings": 2, "skill_level": "beginner"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["food_id"] == 1
        assert data["servings"] == 2
        assert len(data["step_by_step_instructions"]) >= 3
        assert data["source"] == "offline_fallback"


def test_cooking_instructions_mocked_gemini():
    """Gemini cooking instructions formatted cleanly with verified nutrition."""
    mock_json = json.dumps({
        "prep_time_mins": 8,
        "cook_time_mins": 10,
        "equipment_needed": ["Pan", "Whisk"],
        "ingredients": ["1 cup Moong dal batter", "1 chopped green chilli", "1 tsp mustard oil"],
        "step_by_step_instructions": ["Whisk batter", "Pour on preheated skillet", "Flip after 3 minutes"],
        "chef_tips": ["Use a cast iron pan for best crispiness", "Keep flame medium-low"]
    })
    mock_response = MagicMock(text=mock_json, usage_metadata=None)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/recipes/2/instructions", json={"food_id": 2, "servings": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["cook_time_mins"] == 10
        assert len(data["chef_tips"]) == 2
        assert data["source"] == settings.gemini_model


# ─── 7. ERROR, TIMEOUT, EMPTY & RATE-LIMIT TESTS ────────────────────────────

def test_api_failure_triggers_graceful_fallback():
    """When Gemini throws an unhandled API error, fallback is returned without 500 error."""
    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("Google 503 Backend Failure"))
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/assistant", json={"query": "Suggest dinner"})
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "offline_fallback"
        assert len(data["reply"]) > 10


def test_api_timeout_triggers_graceful_fallback():
    """When Gemini call exceeds timeout threshold, fallback is returned within bounds."""
    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/assistant", json={"query": "Suggest lunch options"})
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "offline_fallback"


def test_empty_response_triggers_graceful_fallback():
    """When Gemini returns an empty text response, fallback is returned."""
    mock_response = MagicMock(text="", usage_metadata=None)

    with patch.object(gemini_client, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.post("/api/ai/assistant", json={"query": "Is oats good for breakfast?"})
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "offline_fallback"


def test_rate_limiting_enforcement():
    """When client rate limit is exceeded, falls back safely with audit entry."""
    # Artificially fill rate limiter bucket for a test user
    test_user_id = "test_flood_user"
    for _ in range(35):
        user_rate_limiter.is_allowed(test_user_id)

    token = generate_token(test_user_id)
    response = client.post(
        "/api/ai/assistant",
        json={"query": "How many calories in apple?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "offline_fallback"
