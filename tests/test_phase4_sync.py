"""
DietSense — Phase 4 Local-Cloud Synchronization Test Suite
Verifies:
1. SQLite remains local source of truth for offline operation.
2. Pending synchronization queue (sync_queue) tracking mutations.
3. Full synchronization across all 5 operational entities:
   - profiles
   - meal plans
   - meal logs
   - feedback
   - pantry items
4. Sync status reporting and last-synced timestamps.
5. Manual and automatic trigger endpoints (/api/sync/trigger, /api/sync/status, /api/sync/retry).
6. Retry handling for failed synchronization items.
7. Idempotent synchronization and duplicate record prevention (sqlite_id UNIQUE).
8. Conflict resolution: Last-Write-Wins preventing overwriting newer data with older data.
9. Offline data creation and full recovery after reconnecting.
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
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
from app.core.security import create_access_token
from app.core.sync_service import (
    enqueue_sync_operation,
    get_sync_status,
    sync_user_data,
    retry_failed_sync,
)
from db.database import init_db, get_connection, get_db_cursor

client = TestClient(app)
init_db()


@pytest.fixture
def test_user():
    """Provisions a clean local test user with auth token and returns user details."""
    uid = f"usr_{uuid.uuid4().hex[:12]}"
    email = f"sync_{uuid.uuid4().hex[:8]}@dietsense.ai"
    token = create_access_token(user_id=uid, email=email)
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, '!local_hash', 'Sync Tester', 'active', ?, ?)
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
                ?, ?, ?, 'Sync Tester', 'vegetarian', '[]',
                2000, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', ?
            )
            """,
            (f"prof_{uuid.uuid4().hex[:12]}", uid, email, now),
        )

    return {"id": uid, "email": email, "token": token}


# ─── 1. OFFLINE DATA CREATION & QUEUE ─────────────────────────────────────────

def test_offline_data_creation_enqueues_mutations(test_user):
    """
    Local operations (profile, meal plans, logs, feedback, pantry) update SQLite
    immediately and append to sync_queue without requiring cloud connectivity.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # 1. Update Profile locally
    res_prof = client.put(
        "/api/auth/profile",
        json={"weight_kg": 72.5, "target_calories": 1950},
        headers=headers,
    )
    assert res_prof.status_code == 200

    # 2. Create Meal Plan locally
    res_plan = client.post(
        "/meal-plans",
        json={
            "date": "2026-11-20",
            "target_calories": 1950,
            "items": [{"slot": "lunch", "name": "Dal & Rice"}],
        },
        headers=headers,
    )
    assert res_plan.status_code == 201
    plan_id = res_plan.json()["id"]

    # 3. Create Meal Log locally
    res_log = client.post(
        "/meal-logs",
        json={"meal_id": "meal_101", "status": "eaten", "item_tags": ["dal"]},
        headers=headers,
    )
    assert res_log.status_code == 201

    # 4. Create Feedback locally
    res_fb = client.post(
        "/feedback/",
        json={"meal_id": "meal_102", "status": "skipped", "reason": "time"},
        headers=headers,
    )
    assert res_fb.status_code == 200

    # 5. Add Pantry Item locally
    res_pantry = client.post(
        "/api/pantry/",
        json={"name": "Oats", "category": "Grains & Pulses", "quantity": "1 kg"},
        headers=headers,
    )
    assert res_pantry.status_code == 200

    # Verify SQLite is updated
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        assert cur.fetchone() is not None

        # Verify sync_queue contains pending items
        cur.execute("SELECT entity_type, status FROM sync_queue WHERE user_id = ?", (uid,))
        queue_items = cur.fetchall()
        types = [q["entity_type"] for q in queue_items]
        assert "profile" in types
        assert "meal_plan" in types
        assert "meal_log" in types
        assert "feedback" in types
        assert "pantry_item" in types
        assert all(q["status"] == "pending" for q in queue_items)

    # Check sync status endpoint
    res_status = client.get("/api/sync/status", headers=headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["pending_count"] >= 5


# ─── 2. SUCCESSFUL SYNCHRONIZATION ────────────────────────────────────────────

def test_successful_synchronization_flow(test_user):
    """
    Verifies that triggering sync pushes pending items, marks them 'synced' in queue,
    updates entity synced_at, and records last_synced_at timestamp.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Enqueue a test pantry item
    item_id = f"pantry_{uuid.uuid4().hex[:12]}"
    enqueue_sync_operation(
        user_id=uid,
        entity_type="pantry_item",
        entity_id=item_id,
        operation="UPSERT",
        payload={"id": item_id, "name": "Almonds", "category": "General", "quantity": "200 g"},
    )

    # Mock PostgreSQL connection
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchone.return_value = None  # No existing profile conflict

    with patch("app.core.sync_service.get_pg_connection", return_value=mock_pg_conn):
        res = client.post("/api/sync/trigger", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["result"]["synced_count"] >= 1
        assert data["result"]["failed_count"] == 0

    # Verify item status in SQLite queue is now 'synced'
    with get_db_cursor() as cur:
        cur.execute("SELECT status FROM sync_queue WHERE user_id = ? AND entity_id = ?", (uid, item_id))
        row = cur.fetchone()
        assert row["status"] == "synced"

        cur.execute("SELECT sync_status, last_synced_at FROM sync_metadata WHERE user_id = ?", (uid,))
        meta = cur.fetchone()
        assert meta["sync_status"] == "synced"
        assert meta["last_synced_at"] is not None


# ─── 3. FAILED SYNCHRONIZATION & RESILIENCE ───────────────────────────────────

def test_failed_synchronization_and_resilience(test_user):
    """
    When cloud is unreachable, sync fails gracefully:
    - Local data is never lost or deleted.
    - Error is recorded in sync_metadata.
    - API returns structured response without crashing.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    enqueue_sync_operation(
        user_id=uid,
        entity_type="meal_log",
        entity_id=f"log_{uuid.uuid4().hex[:12]}",
        operation="UPSERT",
        payload={"meal_id": "10", "status": "eaten"},
    )

    # Simulate cloud unreachable (None returned for PG connection)
    with patch("app.core.sync_service.get_pg_connection", return_value=None):
        res = client.post("/api/sync/trigger", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "partial"
        assert data["result"]["success"] is False
        assert "unreachable" in data["result"]["error"].lower() or "connection" in data["result"]["error"].lower()

    # Verify sync_status reports error/offline
    status_info = get_sync_status(uid)
    assert status_info["status"] in ("error", "offline")
    assert status_info["last_error"] is not None


# ─── 4. RETRY HANDLING ───────────────────────────────────────────────────────

def test_retry_handling_resets_and_retries(test_user):
    """
    Verifies that retry_failed_sync resets failed items to pending and re-attempts sync.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    q_id = f"sync_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO sync_queue (
                id, user_id, entity_type, entity_id, operation, payload,
                status, retry_count, max_retries, last_error, created_at, updated_at
            ) VALUES (?, ?, 'pantry_item', 'p_test', 'UPSERT', '{"name": "Rice"}', 'failed', 5, 5, 'Network timeout', ?, ?)
            """,
            (q_id, uid, now, now),
        )

    status_before = get_sync_status(uid)
    assert status_before["failed_count"] == 1

    # Mock PG connection for retry
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchone.return_value = None

    with patch("app.core.sync_service.get_pg_connection", return_value=mock_pg_conn):
        res = client.post("/api/sync/retry", headers=headers)
        assert res.status_code == 200
        assert res.json()["result"]["success"] is True

    # Check that item is now synced
    with get_db_cursor() as cur:
        cur.execute("SELECT status, retry_count FROM sync_queue WHERE id = ?", (q_id,))
        row = cur.fetchone()
        assert row["status"] == "synced"


# ─── 5. DUPLICATE PREVENTION & IDEMPOTENCY ───────────────────────────────────

def test_duplicate_prevention_on_repeated_sync(test_user):
    """
    Running sync repeatedly with the same records must never create duplicates,
    enforced by sqlite_id UNIQUE on PostgreSQL.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    log_id = f"log_{uuid.uuid4().hex[:12]}"
    enqueue_sync_operation(
        user_id=uid,
        entity_type="meal_log",
        entity_id=log_id,
        operation="UPSERT",
        payload={"meal_id": "505", "status": "eaten", "item_tags": ["apple"]},
    )

    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchone.return_value = None

    with patch("app.core.sync_service.get_pg_connection", return_value=mock_pg_conn):
        # First sync
        res1 = client.post("/api/sync/trigger", headers=headers)
        assert res1.status_code == 200

        # Second sync of same item
        enqueue_sync_operation(
            user_id=uid,
            entity_type="meal_log",
            entity_id=log_id,
            operation="UPSERT",
            payload={"meal_id": "505", "status": "eaten", "item_tags": ["apple"]},
        )
        res2 = client.post("/api/sync/trigger", headers=headers)
        assert res2.status_code == 200

        # Verify SQL queries executed included ON CONFLICT (sqlite_id)
        queries = [call[0][0] for call in mock_pg_cur.execute.call_args_list]
        meal_log_upserts = [q for q in queries if "ON CONFLICT (sqlite_id)" in q]
        assert len(meal_log_upserts) >= 1


# ─── 6. CONFLICT RESOLUTION (LAST-WRITE-WINS) ─────────────────────────────────

def test_conflict_resolution_last_write_wins(test_user):
    """
    Conflict resolution:
    - If cloud data has a newer updated_at timestamp than local data,
      the local SQLite record is updated to match the cloud version.
    - Newer data is NEVER overwritten by older data.
    """
    uid = test_user["id"]
    local_time = datetime(2026, 11, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    cloud_time = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)  # Newer in cloud

    # Enqueue an older local profile update
    enqueue_sync_operation(
        user_id=uid,
        entity_type="profile",
        entity_id=uid,
        operation="UPSERT",
        payload={"full_name": "Old Local Name", "target_calories": 1600, "updated_at": local_time},
    )

    # Mock cloud profile having newer timestamp
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchone.return_value = {
        "updated_at": cloud_time,
        "full_name": "Newer Cloud Name",
        "target_calories": 2100,
    }

    with patch("app.core.sync_service.get_pg_connection", return_value=mock_pg_conn):
        sync_user_data(uid)

    # Local SQLite profile must reflect the newer cloud data
    with get_db_cursor() as cur:
        cur.execute("SELECT full_name, target_calories, updated_at FROM profiles WHERE user_id = ?", (uid,))
        prof = cur.fetchone()
        assert prof["full_name"] == "Newer Cloud Name"
        assert prof["target_calories"] == 2100
        assert prof["updated_at"] == cloud_time.isoformat()


# ─── 7. RECOVERY AFTER RECONNECTING ──────────────────────────────────────────

def test_recovery_after_reconnecting(test_user):
    """
    Simulates:
    1. User performs multiple actions offline (queue accumulates).
    2. Sync attempts fail because network is offline.
    3. Network connectivity is restored -> sync triggers and flushes all pending items.
    """
    uid = test_user["id"]
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Accumulate 3 offline items
    for i in range(3):
        enqueue_sync_operation(
            user_id=uid,
            entity_type="pantry_item",
            entity_id=f"pantry_recover_{i}_{uuid.uuid4().hex[:6]}",
            operation="UPSERT",
            payload={"name": f"Item {i}", "quantity": "1 unit"},
        )

    # 1. Sync fails offline
    with patch("app.core.sync_service.get_pg_connection", return_value=None):
        sync_res_offline = client.post("/api/sync/trigger", headers=headers)
        assert sync_res_offline.json()["status"] == "partial"

    # 2. Connection returns
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchone.return_value = None

    with patch("app.core.sync_service.get_pg_connection", return_value=mock_pg_conn):
        sync_res_online = client.post("/api/sync/trigger", headers=headers)
        assert sync_res_online.status_code == 200
        assert sync_res_online.json()["status"] == "success"

    # All items are now synced
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sync_queue WHERE user_id = ? AND status = 'pending'", (uid,))
        assert cur.fetchone()[0] == 0
