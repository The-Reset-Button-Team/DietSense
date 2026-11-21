"""
DietSense — Clear Pantry Functionality Test Suite
Tests:
1. Clearing a populated pantry via DELETE /api/pantry/clear and DELETE /api/pantry/
2. Clearing an already-empty pantry (idempotent, returns 0 deleted)
3. User-specific deletion (clearing User A's pantry never touches User B's inventory)
4. Preserving unrelated tables:
   - User account & profile
   - Saved meal plans
   - Meal history logs
   - User feedback
   - Food catalog and nutritional database
5. Pantry availability indicators and pantry-based recipe recommendations update after clearing
6. Supabase PostgreSQL compatibility:
   - Enqueuing CLEAR_ALL in sync_queue
   - Purging stale pending upserts
   - _sync_pantry_item executing DELETE FROM public.pantry_items WHERE user_id = %s
7. Security: Unauthenticated requests return 401 Unauthorized
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.security import create_access_token
from app.core.sync_service import _sync_pantry_item
from db.database import init_db, get_db_cursor

client = TestClient(app)
init_db()


def create_user_fixture(prefix: str = "clr"):
    """Creates a local user in SQLite and returns user_id, email, and auth headers."""
    uid = f"usr_{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@dietsense.ai"
    token = create_access_token(user_id=uid, email=email)
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, '!test_hash', 'Clear Pantry Tester', 'active', ?, ?)
            """,
            (uid, email, now, now),
        )
        cur.execute(
            """
            INSERT INTO profiles (
                id, user_id, email, full_name, dietary_pref, allergies,
                target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                active_meal_frequency, age, gender, height_cm, weight_kg,
                goal, activity_level, updated_at
            ) VALUES (
                ?, ?, ?, 'Clear Pantry Tester', 'vegetarian', '[]',
                2000, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', ?
            )
            """,
            (f"prof_{uid}", uid, email, now),
        )

    return {"user_id": uid, "email": email, "headers": {"Authorization": f"Bearer {token}"}}


def test_clear_populated_pantry():
    """Clearing a populated pantry deletes all user's items and returns deleted_count."""
    user = create_user_fixture("pop")
    headers = user["headers"]

    # 1. Add 3 items to pantry
    add_res = client.post(
        "/api/pantry/",
        json={
            "items": [
                {"name": "Paneer", "category": "Dairy & Protein", "quantity": "200g"},
                {"name": "Spinach", "category": "Produce", "quantity": "1 bunch"},
                {"name": "Olive Oil", "category": "Pantry Staples", "quantity": "500ml"},
            ]
        },
        headers=headers,
    )
    assert add_res.status_code == 200

    # Verify items exist
    get_res = client.get("/api/pantry/", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) == 3

    # 2. Clear pantry via DELETE /api/pantry/clear
    clear_res = client.delete("/api/pantry/clear", headers=headers)
    assert clear_res.status_code == 200
    data = clear_res.json()
    assert data["status"] == "success"
    assert data["deleted_count"] == 3
    assert "cleared successfully" in data["message"].lower()

    # 3. Verify pantry is now empty
    get_after = client.get("/api/pantry/", headers=headers)
    assert get_after.status_code == 200
    assert len(get_after.json()) == 0

    # 4. Verify in SQLite database directly
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM pantry_items WHERE user_id = ?", (user["user_id"],))
        assert cur.fetchone()["count"] == 0


def test_clear_empty_pantry():
    """Clearing an already-empty pantry is idempotent and succeeds with deleted_count = 0."""
    user = create_user_fixture("empty")
    headers = user["headers"]

    # Verify initially empty
    get_res = client.get("/api/pantry/", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) == 0

    # Clear empty pantry
    clear_res = client.delete("/api/pantry/clear", headers=headers)
    assert clear_res.status_code == 200
    data = clear_res.json()
    assert data["status"] == "success"
    assert data["deleted_count"] == 0
    assert "cleared successfully" in data["message"].lower()

    # Clear again via /api/pantry/
    clear_res_root = client.delete("/api/pantry/", headers=headers)
    assert clear_res_root.status_code == 200
    assert clear_res_root.json()["deleted_count"] == 0


def test_user_specific_pantry_isolation():
    """Clearing User A's pantry never affects User B's pantry inventory."""
    user_a = create_user_fixture("user_a")
    user_b = create_user_fixture("user_b")

    # Add items to User A
    client.post(
        "/api/pantry/",
        json={"items": [{"name": "Milk", "quantity": "1L"}, {"name": "Eggs", "quantity": "6"}]},
        headers=user_a["headers"],
    )

    # Add items to User B
    client.post(
        "/api/pantry/",
        json={"items": [{"name": "Almonds", "quantity": "250g"}, {"name": "Oats", "quantity": "1kg"}]},
        headers=user_b["headers"],
    )

    # Verify both have 2 items
    assert len(client.get("/api/pantry/", headers=user_a["headers"]).json()) == 2
    assert len(client.get("/api/pantry/", headers=user_b["headers"]).json()) == 2

    # User A clears pantry
    clear_res = client.delete("/api/pantry/clear", headers=user_a["headers"])
    assert clear_res.status_code == 200
    assert clear_res.json()["deleted_count"] == 2

    # User A's pantry is now 0
    assert len(client.get("/api/pantry/", headers=user_a["headers"]).json()) == 0

    # User B's pantry MUST STILL have 2 items!
    user_b_items = client.get("/api/pantry/", headers=user_b["headers"]).json()
    assert len(user_b_items) == 2
    b_names = [i["name"] for i in user_b_items]
    assert "Almonds" in b_names
    assert "Oats" in b_names


def test_clear_pantry_does_not_delete_other_data():
    """
    Clearing pantry must NOT delete:
    - User account
    - User profile
    - Saved meal plans
    - Meal history logs
    - User feedback
    - Food catalog records
    """
    user = create_user_fixture("persist")
    uid = user["user_id"]
    headers = user["headers"]
    now = datetime.now(timezone.utc).isoformat()

    # 1. Insert meal plan, meal log, feedback, and pantry items
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO meal_plans (id, user_id, date, target_calories, items, status, created_at)
            VALUES (?, ?, '2026-11-21', 2000, '["test_plan"]', 'generated', ?)
            """,
            (f"plan_{uid}", uid, now),
        )
        cur.execute(
            """
            INSERT INTO meal_logs (id, user_id, meal_id, status, reason, timestamp, created_at)
            VALUES (?, ?, 'meal_1', 'eaten', NULL, ?, ?)
            """,
            (f"log_{uid}", uid, now, now),
        )
        cur.execute(
            """
            INSERT INTO feedback (id, user_id, meal_id, status, feedback_text, created_at)
            VALUES (?, ?, 'meal_1', 'eaten', 'Delicious meal', ?)
            """,
            (f"fb_{uid}", uid, now),
        )

    # Add pantry item
    client.post("/api/pantry/", json={"name": "Atta", "quantity": "5kg"}, headers=headers)
    assert len(client.get("/api/pantry/", headers=headers).json()) == 1

    # Check food catalog has records before clearing
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_foods FROM foods;")
        catalog_count_before = cur.fetchone()["total_foods"]
        assert catalog_count_before > 0

    # 2. Clear pantry
    clear_res = client.delete("/api/pantry/clear", headers=headers)
    assert clear_res.status_code == 200
    assert clear_res.json()["deleted_count"] == 1

    # 3. Verify ALL unrelated data is intact:
    with get_db_cursor() as cur:
        # User account intact
        cur.execute("SELECT id FROM users WHERE id = ?", (uid,))
        assert cur.fetchone() is not None

        # Profile intact
        cur.execute("SELECT id FROM profiles WHERE user_id = ?", (uid,))
        assert cur.fetchone() is not None

        # Meal plans intact
        cur.execute("SELECT id FROM meal_plans WHERE user_id = ?", (uid,))
        assert cur.fetchone() is not None

        # Meal logs intact
        cur.execute("SELECT id FROM meal_logs WHERE user_id = ?", (uid,))
        assert cur.fetchone() is not None

        # Feedback intact
        cur.execute("SELECT id FROM feedback WHERE user_id = ?", (uid,))
        assert cur.fetchone() is not None

        # Food catalog completely untouched
        cur.execute("SELECT COUNT(*) AS total_foods FROM foods;")
        catalog_count_after = cur.fetchone()["total_foods"]
        assert catalog_count_after == catalog_count_before

        # Only pantry items cleared for this user
        cur.execute("SELECT COUNT(*) AS cnt FROM pantry_items WHERE user_id = ?", (uid,))
        assert cur.fetchone()["cnt"] == 0


def test_pantry_recommendations_update_after_clear():
    """Recipe recommendations update their coverage and can_cook_now when pantry is cleared."""
    user = create_user_fixture("rec")
    headers = user["headers"]

    # 1. Add all ingredients for Jeera Paani
    client.post(
        "/api/pantry/",
        json={
            "items": [
                {"name": "Jeera", "inStock": True},
                {"name": "Ajwain", "inStock": True},
                {"name": "Badam", "inStock": True},
            ]
        },
        headers=headers,
    )

    # Recommendations before clear: Jeera recipe has 100% coverage
    rec_res = client.get("/api/pantry/recipe-recommendations", headers=headers)
    assert rec_res.status_code == 200
    top_recipe = rec_res.json()["recipes"][0]
    assert "Jeera" in top_recipe["name"]
    assert top_recipe["can_cook_now"] is True
    assert top_recipe["coverage_pct"] == 100.0

    # 2. Clear pantry
    client.delete("/api/pantry/clear", headers=headers)

    # 3. Recommendations after clear: can_cook_now is False, coverage drops
    rec_res_after = client.get("/api/pantry/recipe-recommendations", headers=headers)
    assert rec_res_after.status_code == 200
    recipes_after = rec_res_after.json()["recipes"]
    for r in recipes_after:
        assert r["can_cook_now"] is False
        assert r["coverage_pct"] == 0.0


def test_supabase_compatibility_and_sync_queue():
    """
    Validates Supabase integration:
    1. Clearing enqueues CLEAR_ALL operation in sync_queue
    2. Clears pending UPSERT operations for this user's pantry items
    3. _sync_pantry_item executes DELETE FROM public.pantry_items WHERE user_id = %s
    """
    user = create_user_fixture("sb")
    uid = user["user_id"]
    headers = user["headers"]

    # Add item
    client.post("/api/pantry/", json={"name": "Curd", "quantity": "400g"}, headers=headers)

    # Clear pantry
    client.delete("/api/pantry/clear", headers=headers)

    # Check sync_queue
    with get_db_cursor() as cur:
        # Pending UPSERTs should be removed
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM sync_queue WHERE user_id = ? AND entity_type = 'pantry_item' AND operation = 'UPSERT' AND status = 'pending'",
            (uid,),
        )
        assert cur.fetchone()["cnt"] == 0

        # CLEAR_ALL operation should be enqueued
        cur.execute(
            "SELECT operation, payload FROM sync_queue WHERE user_id = ? AND entity_type = 'pantry_item' AND operation = 'CLEAR_ALL'",
            (uid,),
        )
        queue_row = cur.fetchone()
        assert queue_row is not None
        assert queue_row["operation"] == "CLEAR_ALL"

    # Test _sync_pantry_item execution with mock PostgreSQL cursor
    mock_pg_cursor = MagicMock()
    mock_cloud_uuid = f"sb_uuid_{uuid.uuid4().hex[:8]}"

    sync_item = {
        "operation": "CLEAR_ALL",
        "entity_id": "all",
        "payload": '{"user_id": "' + uid + '"}',
    }
    _sync_pantry_item(mock_pg_cursor, mock_cloud_uuid, sync_item, cur_sqlite=None)

    # Assert Postgres DELETE was called targeting the user's UUID
    mock_pg_cursor.execute.assert_called_once_with(
        "DELETE FROM public.pantry_items WHERE user_id = %s;",
        (mock_cloud_uuid,),
    )


def test_unauthenticated_clear_fails():
    """Calling clear without authentication returns 401 Unauthorized."""
    res = client.delete("/api/pantry/clear")
    assert res.status_code == 401
