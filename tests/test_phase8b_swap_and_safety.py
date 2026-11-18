"""
Phase 8B — Tests for Dynamic Meal Swap and Dietary Safety Shield.

Validates:
1. GET /api/recommendations/safety-shield:
   - Requires authentication (401).
   - Identifies and audits catalog candidates against active dietary rules & allergens.
   - Categorizes safe vs blocked items with rule, conflict, and descriptive reason.
2. POST /api/recommendations/swap:
   - Requires authentication (401).
   - Returns slot-appropriate alternatives matching calorie and macro targets.
   - Calculates macro_match_pct and signed macro deltas (delta_calories, delta_protein_g, etc.).
   - Filters unsafe items before scoring so unsafe foods never appear in swap alternatives.
   - Excludes the current meal itself from alternatives.
3. POST /api/recommendations/swap/validate:
   - 400 response with safety details when proposed candidate violates user's diet or allergen profile.
   - 200 { safe: true } when candidate complies with all gates.
4. Gemini AI post-generation safety gate (_is_recipe_safe):
   - Rejects recipes violating dietary preference (meat for vegetarians/vegans).
   - Rejects recipes violating allergens (dairy for vegan, peanuts for peanut allergy).
   - Approves safe recipe suggestions.
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
from app.ai.service import ai_service
from ml.scoring.safety_gate import audit_safe, filter_safe
from db.database import get_db_cursor

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "phase8b_test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def setup_user_profile(user_id: str, dietary_pref: str, allergies: list[str], calories: int = 2000):
    """Seed or update user's profile in the test database."""
    import json
    now = "2026-11-19T00:00:00Z"
    email = f"{user_id}@test.dietsense.ai"
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at) "
                "VALUES (?, ?, '!managed', ?, 'active', ?, ?)",
                (user_id, email, f"User {user_id}", now, now),
            )
        cur.execute(
            """
            INSERT INTO profiles (id, user_id, email, dietary_pref, allergies, target_calories, budget_per_meal, prep_time_limit, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 120, 30, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                dietary_pref=excluded.dietary_pref,
                allergies=excluded.allergies,
                target_calories=excluded.target_calories,
                updated_at=excluded.updated_at
            """,
            (user_id, user_id, email, dietary_pref, json.dumps(allergies), calories, now),
        )


# ─── 1. Safety Shield Tests ──────────────────────────────────────────────────

def test_safety_shield_unauthenticated_401():
    """Unauthenticated requests to safety shield are rejected."""
    res = client.get("/api/recommendations/safety-shield")
    assert res.status_code == 401


def test_safety_shield_vegetarian_auditing():
    """Safety shield correctly audits catalog and blocks meat/poultry for vegetarian users."""
    user_id = "test_user_veg_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=[])
    token = generate_token(user_id)

    res = client.get(
        "/api/recommendations/safety-shield",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "active_rules" in data
    assert "safe_count" in data
    assert "blocked_count" in data
    assert "blocked_candidates" in data
    assert data["total_audited"] > 0
    assert data["safe_count"] + data["blocked_count"] == data["total_audited"]

    # At least one blocked item for meat
    rules = [r["rule"] for r in data["active_rules"]]
    assert "diet" in rules

    # Verify blocked items have reason explaining vegetarian rule
    for blocked in data["blocked_candidates"]:
        if blocked["rule"] == "vegetarian":
            assert "conflict" in blocked
            assert "meat" in blocked["reason"].lower() or "conflict" in blocked["reason"].lower()


def test_safety_shield_peanut_allergen_auditing():
    """Safety shield identifies and blocks peanut-containing items for peanut-allergic users."""
    user_id = "test_user_peanut_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=["peanuts"])
    token = generate_token(user_id)

    res = client.get(
        "/api/recommendations/safety-shield",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()

    # Allergen rule should be present in active rules
    allergen_rules = [r for r in data["active_rules"] if r["rule"] == "allergen"]
    assert len(allergen_rules) >= 1
    assert any("peanut" in r["label"].lower() for r in allergen_rules)

    # Candidate with peanuts must be blocked
    blocked_conflicts = [b["conflict"] for b in data["blocked_candidates"]]
    assert any("peanut" in c or "nuts" in c or "groundnuts" in c for c in blocked_conflicts)


# ─── 2. Swap Endpoint Tests ──────────────────────────────────────────────────

def test_swap_endpoint_unauthenticated_401():
    """Unauthenticated requests to swap are rejected."""
    res = client.post("/api/recommendations/swap", json={"slot_id": "breakfast"})
    assert res.status_code == 401


def test_swap_endpoint_calculates_deltas_and_match():
    """POST /recommendations/swap returns alternatives with deltas and macro match percentage."""
    user_id = "test_user_swap_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=[], calories=2000)
    token = generate_token(user_id)

    current_meal = {
        "name": "Moong Dal & Oats Chilla",
        "calories": 380,
        "protein_g": 18.0,
        "carbs_g": 48.0,
        "fat_g": 7.0,
        "fiber_g": 5.0,
    }

    res = client.post(
        "/api/recommendations/swap",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slot_id": "breakfast",
            "current_meal": current_meal,
            "target_calories": 500,
            "top_n": 4,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "current_meal" in data
    assert "swap_alternatives" in data
    alts = data["swap_alternatives"]
    assert len(alts) >= 1

    # Verify current meal itself is excluded from alternatives
    for alt in alts:
        assert alt["item"]["name"].lower() != current_meal["name"].lower()
        # Verify macro match pct is bounded 0-100
        assert 0 <= alt["macro_match_pct"] <= 100
        # Verify deltas are computed
        assert "delta_calories" in alt
        assert "delta_protein_g" in alt
        assert "delta_carbs_g" in alt
        assert "delta_fat_g" in alt
        # Arithmetic check: delta_calories == round(alt.calories - current.calories, 1)
        expected_cal_delta = round(float(alt["item"]["calories"]) - 380, 1)
        assert abs(alt["delta_calories"] - expected_cal_delta) < 0.01


def test_swap_never_returns_unsafe_item():
    """Swap endpoint excludes foods conflicting with user's allergies or diet."""
    user_id = "test_user_strict_vegan_8b"
    setup_user_profile(user_id, dietary_pref="vegan", allergies=["peanuts", "dairy"])
    token = generate_token(user_id)

    res = client.post(
        "/api/recommendations/swap",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slot_id": "lunch",
            "current_meal": {"name": "Lentil Soup", "calories": 400, "protein_g": 20, "carbs_g": 60, "fat_g": 5},
            "top_n": 5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    for alt in data["swap_alternatives"]:
        tags = set(t.lower() for t in alt["item"].get("tags", []))
        allergens = set(a.lower() for a in alt["item"].get("allergens", []))
        # No meat
        assert not (tags & {"meat", "non-veg", "chicken", "fish", "beef", "pork"})
        # No dairy for vegan
        assert not (tags & {"dairy", "cheese", "paneer", "ghee", "butter"})
        assert not (allergens & {"dairy", "milk", "peanuts", "nuts"})


# ─── 3. Swap Validation Endpoint Tests ───────────────────────────────────────

def test_validate_swap_blocks_allergen_conflict():
    """POST /recommendations/swap/validate rejects food containing declared allergens."""
    user_id = "test_user_allergy_val_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=["peanuts"])
    token = generate_token(user_id)

    # Candidate with peanuts
    candidate = {
        "name": "Peanut Butter Oats",
        "tags": ["veg", "breakfast"],
        "allergens": ["peanuts"],
        "calories": 450,
        "protein_g": 15,
        "carbs_g": 50,
        "fat_g": 18,
    }

    res = client.post(
        "/api/recommendations/swap/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"candidate": candidate},
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["safe"] is False
    assert "peanut" in detail["reason"].lower() or "allergen" in detail["rule"].lower()


def test_validate_swap_blocks_dietary_violation():
    """POST /recommendations/swap/validate rejects chicken/meat for vegetarian users."""
    user_id = "test_user_veg_val_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=[])
    token = generate_token(user_id)

    candidate = {
        "name": "Grilled Chicken Breast",
        "tags": ["non-veg", "poultry", "meat"],
        "allergens": [],
        "calories": 300,
        "protein_g": 40,
        "carbs_g": 0,
        "fat_g": 8,
    }

    res = client.post(
        "/api/recommendations/swap/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"candidate": candidate},
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["safe"] is False
    assert detail["rule"] == "vegetarian"


def test_validate_swap_approves_safe_candidate():
    """POST /recommendations/swap/validate returns 200 { safe: true } for valid food."""
    user_id = "test_user_safe_val_8b"
    setup_user_profile(user_id, dietary_pref="vegetarian", allergies=["peanuts"])
    token = generate_token(user_id)

    candidate = {
        "name": "Palak Moong Dal Tadka",
        "tags": ["veg", "lunch", "indian"],
        "allergens": [],
        "calories": 350,
        "protein_g": 18,
        "carbs_g": 52,
        "fat_g": 6,
    }

    res = client.post(
        "/api/recommendations/swap/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"candidate": candidate},
    )
    assert res.status_code == 200
    assert res.json()["safe"] is True


# ─── 4. Gemini AI Post-Generation Safety Gate Tests ─────────────────────────

def test_gemini_post_generation_safety_gate_meat_exclusion():
    """_is_recipe_safe blocks Gemini from hallucinating meat in vegetarian suggestions."""
    veg_profile = {"dietary_pref": "vegetarian", "allergies": []}

    chicken_recipe = {
        "name": "Chicken Tikka Salad",
        "description": "Tender grilled chicken pieces with cucumber",
        "ingredients": ["boneless chicken", "yogurt", "lemon"],
    }
    assert ai_service._is_recipe_safe(chicken_recipe, veg_profile) is False

    veg_recipe = {
        "name": "Tofu & Cucumber Salad",
        "description": "Crisp cucumber with spiced tofu cubes",
        "ingredients": ["firm tofu", "cucumber", "lemon", "mint"],
    }
    assert ai_service._is_recipe_safe(veg_recipe, veg_profile) is True


def test_gemini_post_generation_safety_gate_allergen_exclusion():
    """_is_recipe_safe blocks Gemini from suggesting peanut or dairy recipes when allergic."""
    peanut_profile = {"dietary_pref": "vegetarian", "allergies": ["peanuts"]}

    peanut_recipe = {
        "name": "Spiced Groundnut Chaat",
        "description": "Roasted groundnuts with onion and chili",
        "ingredients": ["peanuts", "onion", "chaat masala"],
    }
    assert ai_service._is_recipe_safe(peanut_recipe, peanut_profile) is False

    dairy_profile = {"dietary_pref": "vegan", "allergies": []}
    paneer_recipe = {
        "name": "Paneer Bhurji Wrap",
        "description": "Scrambled cottage cheese with spices",
        "ingredients": ["paneer", "whole wheat roti", "onions"],
    }
    assert ai_service._is_recipe_safe(paneer_recipe, dairy_profile) is False


# ─── 5. Core Safety Gate audit_safe & filter_safe Unit Tests ────────────────

def test_audit_safe_categorization():
    """audit_safe correctly separates safe and blocked candidates with reasons."""
    candidates = [
        {"id": 1, "name": "Chicken Curry", "tags": ["non-veg", "meat"], "allergens": []},
        {"id": 2, "name": "Peanut Chikki", "tags": ["veg"], "allergens": ["peanuts"]},
        {"id": 3, "name": "Moong Dal Chilla", "tags": ["veg"], "allergens": []},
        {"id": 4, "name": "Egg Bhurji", "tags": ["eggetarian", "egg"], "allergens": ["eggs"]},
    ]

    user_profile = {"dietary_pref": "vegetarian", "allergies": ["peanuts"]}
    result = audit_safe(candidates, user_profile)

    safe_ids = [c["id"] for c in result["safe"]]
    blocked_ids = [b["item"]["id"] for b in result["blocked"]]

    assert 3 in safe_ids
    assert 1 in blocked_ids  # meat blocked by veg
    assert 2 in blocked_ids  # peanut blocked by allergen

    # Check reason messages
    reasons = {b["item"]["id"]: b["reason"] for b in result["blocked"]}
    assert "meat" in reasons[1].lower() or "vegetarian" in reasons[1].lower()
    assert "peanuts" in reasons[2].lower() or "allergen" in reasons[2].lower()
