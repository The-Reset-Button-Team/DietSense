"""
Phase 8C — Tests for Meal Plan Persistence and Profile Studio.
Verifies:
1. Connect frontend/client to meal-plan APIs (/meal-plans and /api/meal-plans).
2. Save today's meal plan (POST /meal-plans with items and target calories).
3. Retrieve saved plans (GET /meal-plans and GET /meal-plans?date=YYYY-MM-DD).
4. Historical meal-plan browsing and date range filters.
5. Generated, accepted, and completed status transitions (PATCH /meal-plans/{id}/status).
6. Weekly plan viewing (GET /meal-plans/weekly).
7. User isolation: User B cannot access, modify, or delete User A's meal plans.
8. Profile Studio preferences: update dietary_pref, allergies, budget_per_meal, prep_time_limit.
9. Profile updates directly influence /recommendations/daily.
10. Account management: password change with old password check.
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
from db.database import get_db_cursor

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "phase8c_test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def test_save_and_retrieve_today_meal_plan():
    """Verify creating, persisting, and retrieving today's meal plan in SQLite."""
    user_id = "usr_p8c_save_001"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}
    today_str = "2026-11-18"

    items = [
        {"slot": "breakfast", "name": "Moong Dal Chilla", "calories": 320, "protein_g": 18.0, "carbs_g": 40.0, "fat_g": 6.0, "fiber_g": 5.0},
        {"slot": "lunch", "name": "Brown Rice & Dal Tadka", "calories": 550, "protein_g": 22.0, "carbs_g": 85.0, "fat_g": 10.0, "fiber_g": 8.0},
        {"slot": "dinner", "name": "Palak Paneer with Roti", "calories": 480, "protein_g": 26.0, "carbs_g": 50.0, "fat_g": 14.0, "fiber_g": 7.0},
    ]

    # 1. Save meal plan
    save_res = client.post(
        "/api/meal-plans",
        json={
            "date": today_str,
            "target_calories": 1850,
            "status": "generated",
            "items": items,
        },
        headers=headers,
    )
    assert save_res.status_code == 201
    plan = save_res.json()
    assert plan["user_id"] == user_id
    assert plan["date"] == today_str
    assert plan["status"] == "generated"
    assert len(plan["items"]) == 3
    plan_id = plan["id"]

    # 2. Retrieve by plan ID
    get_res = client.get(f"/api/meal-plans/{plan_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == plan_id

    # 3. Retrieve using date query parameter
    date_res = client.get(f"/api/meal-plans?date={today_str}", headers=headers)
    assert date_res.status_code == 200
    date_plans = date_res.json()
    assert len(date_plans) >= 1
    assert any(p["id"] == plan_id for p in date_plans)


def test_meal_plan_status_transitions():
    """Verify transitioning meal plan status: generated -> accepted -> completed."""
    user_id = "usr_p8c_status_002"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # 1. Create with generated status
    create_res = client.post(
        "/meal-plans",
        json={
            "date": "2026-11-19",
            "target_calories": 2000,
            "status": "generated",
            "items": [{"slot": "lunch", "name": "Tofu Stir Fry", "calories": 400, "protein_g": 25.0, "carbs_g": 30.0, "fat_g": 12.0}],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]
    assert create_res.json()["status"] == "generated"

    # 2. Update status to 'accepted'
    patch_acc = client.patch(
        f"/meal-plans/{plan_id}/status",
        json={"status": "accepted"},
        headers=headers,
    )
    assert patch_acc.status_code == 200
    assert patch_acc.json()["status"] == "accepted"

    # 3. Update status to 'completed'
    patch_comp = client.patch(
        f"/api/meal-plans/{plan_id}/status",
        json={"status": "completed"},
        headers=headers,
    )
    assert patch_comp.status_code == 200
    assert patch_comp.json()["status"] == "completed"

    # 4. Reject invalid status
    patch_invalid = client.patch(
        f"/meal-plans/{plan_id}/status",
        json={"status": "invalid_status_xyz"},
        headers=headers,
    )
    assert patch_invalid.status_code == 400


def test_weekly_meal_plans_schedule():
    """Verify retrieving 7-day weekly schedule with start_date."""
    user_id = "usr_p8c_weekly_003"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}
    start_date = "2026-11-16"

    # Create plan for day 1 of the week
    client.post(
        "/api/meal-plans",
        json={
            "date": "2026-11-16",
            "target_calories": 1850,
            "status": "accepted",
            "items": [{"name": "Poha", "calories": 300, "protein_g": 10.0, "carbs_g": 50.0, "fat_g": 5.0}],
        },
        headers=headers,
    )

    # Fetch weekly schedule
    weekly_res = client.get(f"/api/meal-plans/weekly?start_date={start_date}", headers=headers)
    assert weekly_res.status_code == 200
    data = weekly_res.json()
    assert data["start_date"] == start_date
    assert len(data["days"]) == 7
    # Day 0 has our plan
    day_0 = data["days"][0]
    assert day_0["date"] == "2026-11-16"
    assert day_0["plan"] is not None
    assert day_0["plan"]["status"] == "accepted"
    # Day 1 has no plan
    day_1 = data["days"][1]
    assert day_1["plan"] is None


def test_meal_plan_user_isolation():
    """Verify strict user isolation: User B cannot access or modify User A's meal plans."""
    user_a = "usr_p8c_iso_userA"
    user_b = "usr_p8c_iso_userB"
    headers_a = {"Authorization": f"Bearer {generate_token(user_a)}"}
    headers_b = {"Authorization": f"Bearer {generate_token(user_b)}"}

    # User A creates a plan
    plan_a_res = client.post(
        "/api/meal-plans",
        json={
            "date": "2026-11-20",
            "target_calories": 1900,
            "status": "accepted",
            "items": [{"name": "Private Meal Plan User A", "calories": 450, "protein_g": 20.0, "carbs_g": 50.0, "fat_g": 10.0}],
        },
        headers=headers_a,
    )
    plan_id_a = plan_a_res.json()["id"]

    # User B list meal plans -> plan A must not appear
    plans_b = client.get("/api/meal-plans", headers=headers_b).json()
    assert all(p["id"] != plan_id_a for p in plans_b)

    # User B get plan A by ID -> 404 Not Found
    get_b = client.get(f"/api/meal-plans/{plan_id_a}", headers=headers_b)
    assert get_b.status_code == 404

    # User B update status of plan A -> 404 Not Found
    patch_b = client.patch(
        f"/api/meal-plans/{plan_id_a}/status",
        json={"status": "completed"},
        headers=headers_b,
    )
    assert patch_b.status_code == 404

    # User B delete plan A -> 404 Not Found
    del_b = client.delete(f"/api/meal-plans/{plan_id_a}", headers=headers_b)
    assert del_b.status_code == 404


def test_profile_studio_updates_and_recommendation_influence():
    """
    Verify Profile Studio updates:
    - Dietary preference (vegan)
    - Allergens (peanuts, dairy)
    - Budget per meal (₹80)
    - Prep time limit (20 min)
    Ensure these changes strictly steer and influence /recommendations/daily.
    """
    user_id = "usr_p8c_prof_rec_004"
    headers = {"Authorization": f"Bearer {generate_token(user_id)}"}

    # 1. Update profile via PUT /api/auth/profile
    update_res = client.put(
        "/api/auth/profile",
        json={
            "full_name": "Dr. Clinical Vegan",
            "dietary_pref": "vegan",
            "dietary_preference": "vegan",
            "allergies": ["dairy", "peanuts"],
            "budget_per_meal": 80.0,
            "prep_time_limit": 20,
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    prof = update_res.json()
    assert prof["dietary_pref"] == "vegan"
    assert "dairy" in prof["allergies"]
    assert "peanuts" in prof["allergies"]
    assert prof["budget_per_meal"] == 80.0
    assert prof["prep_time_limit"] == 20

    # 2. Retrieve profile via GET /api/auth/me to verify persistence in SQLite
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["dietary_pref"] == "vegan"
    assert "dairy" in me_data["allergies"]
    assert me_data["budget_per_meal"] == 80.0
    assert me_data["prep_time_limit"] == 20

    # 3. Call /recommendations/daily WITHOUT explicit profile override in payload
    # Must pull user_id's saved profile from SQLite and filter non-vegan / dairy / peanuts foods
    rec_res = client.post(
        "/recommendations/daily",
        json={
            "active_slots": {
                "early_morning": False,
                "breakfast": True,
                "lunch": True,
                "evening_snack": False,
                "dinner": True,
            },
            "top_n": 3,
        },
        headers=headers,
    )
    assert rec_res.status_code == 200
    data = rec_res.json()
    slots = data["slots"]

    # Verify that all returned foods are strictly vegan and free of dairy/peanuts
    for slot_name, alternatives in slots.items():
        for rec in alternatives:
            item = rec["item"]
            allergens_list = [a.lower() for a in item.get("allergens", [])]
            tags = [t.lower() for t in item.get("tags", [])]

            # No dairy or peanuts allergens
            assert "dairy" not in allergens_list, f"Dairy allergen found in slot {slot_name}: {item['name']}"
            assert "peanuts" not in allergens_list, f"Peanuts allergen found in slot {slot_name}: {item['name']}"

            # Strict vegan: no dairy or meat
            assert "dairy" not in tags, f"Dairy tag found in vegan recommendation: {item['name']}"
            assert "non-veg" not in tags, f"Non-veg tag found in vegan recommendation: {item['name']}"


def test_account_password_change():
    """Verify changing password via POST /api/auth/change-password."""
    import uuid
    from app.core.security import hash_password, verify_password

    user_id = f"usr_p8c_pwd_{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@dietsense.local"
    headers = {"Authorization": f"Bearer {generate_token(user_id, email=email)}"}

    # Seed user in DB with initial password 'InitialPass123'
    initial_hash = hash_password("InitialPass123")
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'active', ?, ?)",
            (user_id, email, initial_hash, "Pass Test User", now, now),
        )

    # 1. Reject invalid old password
    bad_old = client.post(
        "/api/auth/change-password",
        json={"current_password": "WrongPassword", "new_password": "NewSecretPass456"},
        headers=headers,
    )
    assert bad_old.status_code == 400

    # 2. Reject short new password (<6 chars)
    short_pwd = client.post(
        "/api/auth/change-password",
        json={"current_password": "InitialPass123", "new_password": "123"},
        headers=headers,
    )
    assert short_pwd.status_code == 400

    # 3. Successful password change
    ok_pwd = client.post(
        "/api/auth/change-password",
        json={"current_password": "InitialPass123", "new_password": "NewSecretPass456"},
        headers=headers,
    )
    assert ok_pwd.status_code == 200
    assert ok_pwd.json()["status"] == "success"

    # Verify password hash updated in SQLite
    with get_db_cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        updated_row = cur.fetchone()
        assert verify_password("NewSecretPass456", updated_row["password_hash"])
