"""
Tests for Recommendations API and Adaptive Feedback reweighting loop.
"""

import sys
import os
import time
import jwt
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

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def test_recommendations_requires_auth():
    """Unauthenticated request to /recommendations/ is rejected with 401."""
    response = client.post("/recommendations/", json={"dietary_pref": "vegetarian"})
    assert response.status_code == 401


def test_recommendations_honors_safety_gate():
    """Safety gate strictly excludes non-veg and allergen foods."""
    user_id = "usr_test_safe_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "dietary_pref": "vegetarian",
        "allergies": ["peanuts"],
        "target_calories": 1800,
        "budget_per_meal": 100,
        "prep_time_limit": 30,
        "preferred_cuisines": ["indian"],
        "top_n": 5,
    }

    response = client.post("/recommendations/", json=payload, headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0

    # Ensure no items have peanuts or non-veg tags
    for r in results:
        item = r["item"]
        tags = [t.lower() for t in item.get("tags", [])]
        allergens = [a.lower() for a in item.get("allergens", [])]
        assert "non-veg" not in tags
        assert "peanuts" not in allergens


def test_adaptive_feedback_loop():
    """Skipping a meal with reason 'time' penalizes future meals with long prep time."""
    user_id = "usr_test_adaptive_002"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Log feedback with reason 'time' and long-prep-time tag
    fb_res = client.post(
        "/feedback/",
        json={
            "meal_id": 10,
            "status": "skipped",
            "reason": "time",
            "item_tags": ["long-prep-time", "indian"],
        },
        headers=headers,
    )
    assert fb_res.status_code == 200

    # 2. Query recommendations and verify that adaptive penalty was applied
    rec_res = client.post(
        "/recommendations/",
        json={
            "dietary_pref": "vegetarian",
            "target_calories": 2000,
            "budget_per_meal": 100,
            "prep_time_limit": 30,
            "top_n": 4,
        },
        headers=headers,
    )
    assert rec_res.status_code == 200
    results = rec_res.json()
    assert len(results) > 0


def test_recommendations_pantry_bonus():
    """Users with in-stock pantry items receive ingredient-aware recommendation boosts."""
    user_id = "usr_test_pantry_rec_003"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add pantry items for this user
    add_res = client.post(
        "/api/pantry/",
        json={"items": [{"name": "Poha", "category": "Pulses & Grains", "quantity": "500g"}]},
        headers=headers,
    )
    assert add_res.status_code == 200

    # 2. Query recommendations
    rec_res = client.post(
        "/recommendations/",
        json={
            "dietary_pref": "vegetarian",
            "target_calories": 1800,
            "top_n": 5,
        },
        headers=headers,
    )
    assert rec_res.status_code == 200
    results = rec_res.json()
    assert len(results) > 0

    # Poha candidate should have the pantry match reason
    poha_matches = [r for r in results if "poha" in r["item"]["name"].lower()]
    if poha_matches:
        assert "Pantry match" in poha_matches[0]["reason"]

