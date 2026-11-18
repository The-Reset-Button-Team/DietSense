"""
Phase 8A — Tests for Daily Meal Plan Recommendations and Per-Slot Shuffling.
Verifies:
1. Connect daily meal plan to the recommendation API (/recommendations/daily).
2. Generate 3–5 meal alternatives per meal slot.
3. Per-slot shuffle functionality.
4. Daily nutrition totals calculation.
5. Dietary restrictions and allergen filtering before scoring.
6. Actual database nutritional values from SQLite foods catalog.
7. Unauthenticated requests are rejected with 401.
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


def generate_token(user_id: str, email: str = "phase8a_test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


_DEFAULT_PROFILE = {
    "dietary_pref": "vegetarian",
    "target_calories": 1850,
    "budget_per_meal": 120,
    "prep_time_limit": 30,
    "allergies": [],
}


def test_daily_endpoint_requires_auth():
    """Unauthenticated requests to /recommendations/daily are rejected with 401."""
    res = client.post("/recommendations/daily", json={"user_profile": _DEFAULT_PROFILE})
    assert res.status_code == 401

    api_res = client.post("/api/recommendations/daily", json={"user_profile": _DEFAULT_PROFILE})
    assert api_res.status_code == 401


def test_daily_endpoint_returns_3_to_5_alternatives_per_active_slot():
    """POST /recommendations/daily returns 3-5 real alternatives for each active slot."""
    user_id = "usr_phase8a_001"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    payload = {
        "user_profile": _DEFAULT_PROFILE,
        "active_slots": {
            "early_morning": False,
            "breakfast": True,
            "lunch": True,
            "evening_snack": False,
            "dinner": True,
        },
        "top_n": 5,
    }

    res = client.post("/recommendations/daily", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "slots" in data
    assert "totals" in data

    slots = data["slots"]
    assert "breakfast" in slots
    assert "lunch" in slots
    assert "dinner" in slots
    assert "early_morning" not in slots
    assert "evening_snack" not in slots

    for slot_name in ["breakfast", "lunch", "dinner"]:
        alts = slots[slot_name]
        assert 3 <= len(alts) <= 5, f"{slot_name} should have 3-5 alternatives, got {len(alts)}"
        for alt in alts:
            assert "item" in alt
            assert "score" in alt
            assert "breakdown" in alt
            assert "reason" in alt
            item = alt["item"]
            assert item["id"] > 0
            assert len(item["name"]) > 0
            assert item["calories"] > 0
            assert item["protein_g"] >= 0
            assert item["carbs_g"] >= 0
            assert item["fat_g"] >= 0
            assert "fiber_g" in item


def test_daily_endpoint_calculates_daily_totals():
    """Totals object sums the nutrition values of the first recommendation per slot."""
    user_id = "usr_phase8a_002"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    payload = {
        "user_profile": _DEFAULT_PROFILE,
        "active_slots": {
            "breakfast": True,
            "lunch": True,
            "dinner": True,
        },
    }

    res = client.post("/recommendations/daily", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    totals = data["totals"]
    assert totals["calories"] > 0
    assert totals["protein_g"] > 0
    assert totals["carbs_g"] > 0
    assert totals["fat_g"] > 0

    # Verify totals match sum of first item of each active slot
    expected_cals = sum(data["slots"][s][0]["item"]["calories"] for s in data["slots"])
    assert abs(totals["calories"] - expected_cals) <= 2  # due to rounding


def test_daily_endpoint_honors_dietary_restrictions_and_allergens():
    """Vegetarian user with peanut and dairy allergies receives no non-veg, peanut, or dairy items."""
    user_id = "usr_phase8a_003"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    payload = {
        "user_profile": {
            "dietary_pref": "vegetarian",
            "allergies": ["peanuts", "dairy"],
            "target_calories": 1800,
        },
        "active_slots": {
            "breakfast": True,
            "lunch": True,
            "dinner": True,
        },
    }

    res = client.post("/recommendations/daily", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    for slot_name, alts in data["slots"].items():
        for alt in alts:
            item = alt["item"]
            tags = [t.lower() for t in item.get("tags", [])]
            allergens = [a.lower() for a in item.get("allergens", [])]
            assert "non-veg" not in tags, f"Found non-veg item in {slot_name}: {item['name']}"
            assert "peanuts" not in allergens, f"Found peanut allergen in {slot_name}: {item['name']}"
            assert "dairy" not in allergens, f"Found dairy allergen in {slot_name}: {item['name']}"


def test_slot_shuffle_returns_recommendations():
    """Calling /recommendations/slot/{slot_id} with shuffle=True returns valid alternatives."""
    user_id = "usr_phase8a_004"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    res = client.post(
        "/recommendations/slot/lunch?shuffle=true",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert res.status_code == 200
    recs = res.json()
    assert 3 <= len(recs) <= 5
    for rec in recs:
        assert rec["item"]["calories"] > 0
        assert rec["score"] >= 0.0
