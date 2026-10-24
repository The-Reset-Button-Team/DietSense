"""
Tests for Meal Plans, Meal Logs, Analytics, and Profile Endpoints
as defined in the DietSense Workflow Brief.
"""

import sys
import os
import time
import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "user@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def test_profile_get_and_put():
    """Verify GET and PUT on /profile store user constraints under verified user."""
    user_id = "usr_profile_test_001"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # 1. Update profile
    put_res = client.put(
        "/profile",
        json={
            "dietary_pref": "vegan",
            "allergies": ["dairy", "gluten"],
            "target_calories": 1900,
            "budget_per_meal": 120,
            "prep_time_limit": 20,
        },
        headers=headers,
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["dietary_pref"] == "vegan"
    assert data["target_calories"] == 1900

    # 2. Retrieve profile
    get_res = client.get("/profile", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["dietary_pref"] == "vegan"
    assert get_res.json()["budget_per_meal"] == 120


def test_meal_plans_crud():
    """Verify creating and listing meal plans on /meal-plans."""
    user_id = "usr_plan_test_002"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # 1. Create a meal plan
    create_res = client.post(
        "/meal-plans",
        json={
            "date": "2026-10-24",
            "target_calories": 2000,
            "items": [
                {"recipe_id": 1, "name": "Vegetable Poha", "meal_type": "breakfast"},
                {"recipe_id": 3, "name": "Brown Rice Dal", "meal_type": "lunch"},
            ],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    plan = create_res.json()
    assert plan["user_id"] == user_id
    assert len(plan["items"]) == 2
    plan_id = plan["id"]

    # 2. List meal plans
    list_res = client.get("/meal-plans", headers=headers)
    assert list_res.status_code == 200
    user_plans = list_res.json()
    assert len(user_plans) >= 1
    assert any(p["id"] == plan_id for p in user_plans)


def test_meal_logs_and_skip_reason_validation():
    """Verify logging meals and validation of status and skip reasons."""
    user_id = "usr_log_test_003"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # 1. Valid eaten meal log
    eaten_res = client.post(
        "/meal-logs",
        json={"meal_id": 1, "status": "eaten"},
        headers=headers,
    )
    assert eaten_res.status_code == 201
    assert eaten_res.json()["logged"]["status"] == "eaten"

    # 2. Valid skipped meal with reason 'time'
    skip_res = client.post(
        "/meal-logs",
        json={"meal_id": 2, "status": "skipped", "reason": "time", "item_tags": ["long-prep-time"]},
        headers=headers,
    )
    assert skip_res.status_code == 201
    assert skip_res.json()["logged"]["reason"] == "time"

    # 3. Invalid status should be rejected
    invalid_status = client.post(
        "/meal-logs",
        json={"meal_id": 3, "status": "invalid_status"},
        headers=headers,
    )
    assert invalid_status.status_code == 422

    # 4. Invalid skip reason should be rejected
    invalid_reason = client.post(
        "/meal-logs",
        json={"meal_id": 3, "status": "skipped", "reason": "bad_reason"},
        headers=headers,
    )
    assert invalid_reason.status_code == 422


def test_analytics_calculations():
    """Verify /analytics computes real adherence and trend rates without fakes."""
    user_id = "usr_analytics_test_004"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # Log 3 eaten, 1 skipped (reason: time)
    client.post("/meal-logs", json={"meal_id": 1, "status": "eaten"}, headers=headers)
    client.post("/meal-logs", json={"meal_id": 2, "status": "eaten"}, headers=headers)
    client.post("/meal-logs", json={"meal_id": 3, "status": "eaten"}, headers=headers)
    client.post("/meal-logs", json={"meal_id": 4, "status": "skipped", "reason": "time"}, headers=headers)

    analytics_res = client.get("/analytics", headers=headers)
    assert analytics_res.status_code == 200
    data = analytics_res.json()

    assert data["total_logged"] == 4
    assert data["eaten_count"] == 3
    assert data["skipped_count"] == 1
    assert data["adherence_rate_pct"] == 75.0
    assert data["skip_reasons"]["time"] == 1
    assert data["has_data"] is True


def test_vectorizer_edge_cases():
    """Test TF-IDF vectorizer handles empty candidates and empty vocabulary safely."""
    from ml.recommendation.vectorizer import get_similarity

    # Empty candidates
    res_empty = get_similarity({"dietary_pref": "vegetarian"}, [])
    assert len(res_empty) == 0

    # Stop words only (empty vocabulary)
    res_stopwords = get_similarity(
        {"dietary_pref": "the a an"},
        [{"name": "is was", "tags": ["in", "on"], "cuisine": "at"}],
    )
    assert len(res_stopwords) == 1
    assert res_stopwords[0] == 0.0


def test_safety_gate_unknown_allergens_treated_conservatively():
    """Unknown allergen data is excluded when user has declared allergies."""
    from ml.scoring.safety_gate import filter_safe

    candidates = [
        {"name": "Known Safe Item", "allergens": ["dairy"], "tags": ["veg"]},
        {"name": "Unknown Allergen Item", "allergens": None, "tags": ["veg"]},
        {"name": "Explicit Unknown Item", "allergens": [], "allergen_info_unknown": True, "tags": ["veg"]},
    ]

    # User with allergy to nuts
    user_profile = {"dietary_pref": "vegetarian", "allergies": ["nuts"]}
    safe = filter_safe(candidates, user_profile)

    # Only "Known Safe Item" has verified non-nut allergens
    assert len(safe) == 1
    assert safe[0]["name"] == "Known Safe Item"
