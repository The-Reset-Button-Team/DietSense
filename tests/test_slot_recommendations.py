"""
Tests for the POST /recommendations/slot/{slot_id} endpoint.
Verifies per-slot candidate filtering, nutritional data integrity, and error
handling for unknown slot identifiers.
"""

import sys
import os
import time
import jwt
import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------
# Path setup — mirrors the pattern used in test_recommendations.py
# ------------------------------------------------------------------
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


def generate_token(user_id: str, email: str = "slot_test@dietsense.ai") -> str:
    """Create a signed JWT for the given user_id — same approach as test_recommendations.py."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


# ── Shared user profile used by most slot tests ──────────────────────────────
_DEFAULT_PROFILE = {
    "dietary_pref": "vegetarian",
    "target_calories": 1800,
    "budget_per_meal": 120,
    "prep_time_limit": 30,
    "preferred_cuisines": ["indian"],
}


def test_slot_endpoint_requires_auth():
    """Unauthenticated requests to the slot endpoint are rejected with 401."""
    response = client.post(
        "/recommendations/slot/breakfast",
        json=_DEFAULT_PROFILE,
    )
    assert response.status_code == 401


def test_breakfast_slot_returns_at_most_five_results():
    """POST /recommendations/slot/breakfast returns ≤ 5 results."""
    user_id = "usr_slot_test_breakfast_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/breakfast",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert isinstance(results, list)
    assert len(results) <= 5


def test_breakfast_slot_result_structure():
    """Each breakfast result has the required fields."""
    user_id = "usr_slot_test_breakfast_002"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/breakfast",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200
    results = response.json()

    for rec in results:
        assert "item" in rec
        assert "score" in rec
        assert "breakdown" in rec
        assert "reason" in rec
        item = rec["item"]
        # Required nutritional fields
        assert "calories" in item
        assert "protein_g" in item
        assert "carbs_g" in item
        assert "fat_g" in item


def test_dinner_slot_returns_real_nutritional_data():
    """POST /recommendations/slot/dinner returns results with real nutritional data (calories > 0)."""
    user_id = "usr_slot_test_dinner_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/dinner",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    results = response.json()

    # Must return at least one result
    assert len(results) > 0

    # Every result must have positive calorie values (real DB data, not zeroed)
    for rec in results:
        item = rec["item"]
        assert item.get("calories", 0) > 0, (
            f"Expected calories > 0 for item '{item.get('name')}', got {item.get('calories')}"
        )


def test_dinner_slot_respects_five_result_cap():
    """POST /recommendations/slot/dinner returns ≤ 5 results."""
    user_id = "usr_slot_test_dinner_002"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/dinner",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json()) <= 5


def test_unknown_slot_returns_400():
    """POST /recommendations/slot/unknown_slot returns 400, not 500."""
    user_id = "usr_slot_test_unknown_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/unknown_slot",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    # Must NOT be a server error; either 400 (preferred) or empty-list 200
    assert response.status_code in (400, 200), (
        f"Expected 400 or 200 for unknown slot, got {response.status_code}"
    )
    if response.status_code == 200:
        assert response.json() == []


def test_early_morning_slot_returns_results():
    """POST /recommendations/slot/early_morning returns valid results."""
    user_id = "usr_slot_test_em_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/early_morning",
        json={**_DEFAULT_PROFILE, "dietary_pref": "vegan"},
        headers=headers,
    )
    # Acceptable outcomes: 200 with list (may be empty if safety gate is strict)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) <= 5


def test_evening_snack_slot_returns_results():
    """POST /recommendations/slot/evening_snack returns ≤ 5 valid results."""
    user_id = "usr_slot_test_snack_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/evening_snack",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) <= 5


def test_lunch_slot_returns_results_with_nutrition():
    """POST /recommendations/slot/lunch returns results with positive calorie values."""
    user_id = "usr_slot_test_lunch_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/recommendations/slot/lunch",
        json=_DEFAULT_PROFILE,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert len(results) > 0
    for rec in results:
        assert rec["item"].get("calories", 0) > 0
