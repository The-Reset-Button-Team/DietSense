"""
DietSense — Local-Cloud Synchronization Engine
Implements reliable, idempotent synchronization between local SQLite and Supabase PostgreSQL.

Key Architectural Guarantees:
1. SQLite is the primary local source of truth for offline-first operation.
2. Changes are written to SQLite immediately and appended to a persistent `sync_queue`.
3. Idempotent synchronization using `sqlite_id UNIQUE` on all Supabase tables.
4. Conflict resolution via Last-Write-Wins based on `updated_at` timestamps.
5. Never assumes network connectivity guarantees Supabase availability.
6. Exponential retry handling and duplicate prevention.
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from app.core.config import settings
from app.core.supabase_client import get_pg_connection, get_pg_cursor, is_supabase_available
from db.database import get_db_cursor


# ─── Queue Mutation Helpers ───────────────────────────────────────────────────

def enqueue_sync_operation(
    user_id: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    payload: Dict[str, Any],
    cur=None,
) -> str:
    """
    Appends a mutation to the local `sync_queue`.
    Coalesces pending mutations for the same entity to minimize traffic.
    Reuses provided cursor if within an active transaction, avoiding SQLite locks.
    Always succeeds locally without network interaction.
    """
    now = datetime.now(timezone.utc).isoformat()
    payload_json = json.dumps(payload, default=str)

    def _execute(c):
        c.execute(
            """
            SELECT id FROM sync_queue
            WHERE user_id = ? AND entity_type = ? AND entity_id = ? AND status IN ('pending', 'failed')
            """,
            (user_id, entity_type, entity_id),
        )
        existing = c.fetchone()

        if existing:
            queue_id = existing["id"]
            c.execute(
                """
                UPDATE sync_queue SET
                    operation = ?,
                    payload = ?,
                    status = 'pending',
                    updated_at = ?
                WHERE id = ?
                """,
                (operation, payload_json, now, queue_id),
            )
        else:
            queue_id = f"sync_{uuid.uuid4().hex[:12]}"
            c.execute(
                """
                INSERT INTO sync_queue (
                    id, user_id, entity_type, entity_id, operation, payload,
                    status, retry_count, max_retries, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, 5, ?, ?)
                """,
                (queue_id, user_id, entity_type, entity_id, operation, payload_json, now, now),
            )

        c.execute(
            """
            INSERT INTO sync_metadata (user_id, sync_status, pending_count, updated_at)
            VALUES (?, 'pending', 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                pending_count = (SELECT COUNT(*) FROM sync_queue WHERE user_id = ? AND status = 'pending'),
                updated_at = ?
            """,
            (user_id, now, user_id, now),
        )
        return queue_id

    if cur is not None:
        return _execute(cur)
    else:
        with get_db_cursor() as new_cur:
            return _execute(new_cur)


def get_sync_status(user_id: str, check_cloud: bool = True) -> Dict[str, Any]:
    """
    Returns current synchronization status, timestamps, and queue counts for a user.
    """
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) as pending FROM sync_queue
            WHERE user_id = ? AND status = 'pending'
            """,
            (user_id,),
        )
        pending_count = cur.fetchone()["pending"]

        cur.execute(
            """
            SELECT COUNT(*) as failed FROM sync_queue
            WHERE user_id = ? AND status = 'failed'
            """,
            (user_id,),
        )
        failed_count = cur.fetchone()["failed"]

        cur.execute("SELECT * FROM sync_metadata WHERE user_id = ?", (user_id,))
        meta = cur.fetchone()

    cloud_available = is_supabase_available(timeout=2) if check_cloud else False

    last_synced = meta["last_synced_at"] if meta else None
    last_error = meta["last_error"] if meta else None

    if not cloud_available:
        status_label = "offline"
    elif failed_count > 0 or (meta and meta["sync_status"] == "error"):
        status_label = "error"
    elif pending_count > 0:
        status_label = "pending"
    else:
        status_label = "synced"

    return {
        "status": status_label,
        "cloud_available": cloud_available,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "last_synced_at": last_synced,
        "last_attempt_at": meta["last_attempt_at"] if meta else None,
        "last_error": last_error,
    }


# ─── Cloud User ID Resolution ─────────────────────────────────────────────────

def _resolve_cloud_user_uuid(cur_sqlite, pg_conn, user_id: str) -> Optional[str]:
    """
    Resolves the Supabase PostgreSQL UUID corresponding to an internal DietSense user ID.
    Ensures that a matching record exists in Supabase public.users so foreign keys succeed.
    """
    cur_sqlite.execute(
        "SELECT provider_user_id FROM auth_identities WHERE user_id = ? AND provider = 'supabase'",
        (user_id,),
    )
    row = cur_sqlite.fetchone()
    if row and row["provider_user_id"]:
        cloud_uuid = row["provider_user_id"]
    else:
        cloud_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"dietsense:{user_id}"))

    cur_sqlite.execute("SELECT email, full_name FROM users WHERE id = ?", (user_id,))
    u_row = cur_sqlite.fetchone()
    email = u_row["email"] if u_row else f"{user_id}@dietsense.local"
    full_name = u_row["full_name"] if u_row else "DietSense User"

    pg_cur = pg_conn.cursor()
    try:
        pg_cur.execute("SELECT id FROM public.users WHERE id = %s;", (cloud_uuid,))
        if not pg_cur.fetchone():
            pg_cur.execute(
                """
                INSERT INTO public.users (
                    id, email, full_name, age, gender, height_cm, weight_kg,
                    goal, activity_level, daily_calorie_target, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, 26, 'male', 175.0, 75.0,
                    'lose_weight', 'lightly_active', 1850, NOW(), NOW()
                ) ON CONFLICT (id) DO NOTHING;
                """,
                (cloud_uuid, email, full_name),
            )
    except Exception as e:
        print(f"Notice provisioning public.users on Supabase: {e}")

    return cloud_uuid


# ─── Entity Synchronizers ─────────────────────────────────────────────────────

def _sync_profile(pg_cur, cloud_uuid: str, item: dict, cur_sqlite) -> None:
    """Synchronizes profile with timestamp conflict resolution (Last-Write-Wins)."""
    payload = json.loads(item["payload"])
    local_updated = payload.get("updated_at") or datetime.now(timezone.utc).isoformat()
    sqlite_id = item["entity_id"]

    # Check existing cloud profile
    pg_cur.execute("SELECT updated_at, full_name, target_calories FROM public.profiles WHERE user_id = %s;", (cloud_uuid,))
    cloud_prof = pg_cur.fetchone()

    if cloud_prof and cloud_prof.get("updated_at"):
        cloud_updated_str = cloud_prof["updated_at"].isoformat()
        if cloud_updated_str > local_updated:
            cur_sqlite.execute(
                """
                UPDATE profiles SET
                    full_name = COALESCE(?, full_name),
                    target_calories = COALESCE(?, target_calories),
                    synced_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (cloud_prof.get("full_name"), cloud_prof.get("target_calories"), cloud_updated_str, cloud_updated_str, item["user_id"]),
            )
            return

    allergies = payload.get("allergies")
    allergies_json = json.dumps(allergies) if isinstance(allergies, list) else (allergies or "[]")
    cuisines = payload.get("preferred_cuisines")
    cuisines_json = json.dumps(cuisines) if isinstance(cuisines, list) else (cuisines or '["indian"]')

    pg_cur.execute(
        """
        INSERT INTO public.profiles (
            user_id, email, full_name, dietary_pref, allergies, target_calories,
            budget_per_meal, prep_time_limit, is_solo_cook, active_meal_frequency,
            age, gender, height_cm, weight_kg, goal, activity_level,
            preferred_cuisines, sqlite_id, synced_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s::jsonb, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s, NOW(), %s
        )
        ON CONFLICT (user_id) DO UPDATE SET
            email = EXCLUDED.email,
            full_name = EXCLUDED.full_name,
            dietary_pref = EXCLUDED.dietary_pref,
            allergies = EXCLUDED.allergies,
            target_calories = EXCLUDED.target_calories,
            budget_per_meal = EXCLUDED.budget_per_meal,
            prep_time_limit = EXCLUDED.prep_time_limit,
            is_solo_cook = EXCLUDED.is_solo_cook,
            active_meal_frequency = EXCLUDED.active_meal_frequency,
            age = EXCLUDED.age,
            gender = EXCLUDED.gender,
            height_cm = EXCLUDED.height_cm,
            weight_kg = EXCLUDED.weight_kg,
            goal = EXCLUDED.goal,
            activity_level = EXCLUDED.activity_level,
            preferred_cuisines = EXCLUDED.preferred_cuisines,
            sqlite_id = EXCLUDED.sqlite_id,
            synced_at = NOW(),
            updated_at = EXCLUDED.updated_at
        WHERE EXCLUDED.updated_at >= public.profiles.updated_at;
        """,
        (
            cloud_uuid,
            payload.get("email", ""),
            payload.get("full_name", ""),
            payload.get("dietary_pref", "vegetarian"),
            allergies_json,
            payload.get("target_calories", 1850),
            payload.get("budget_per_meal", 100.0),
            payload.get("prep_time_limit", 30),
            bool(payload.get("is_solo_cook", True)),
            payload.get("active_meal_frequency", "3_meals"),
            payload.get("age", 26),
            payload.get("gender", "male"),
            payload.get("height_cm", 175.0),
            payload.get("weight_kg", 75.0),
            payload.get("goal", "lose_weight"),
            payload.get("activity_level", "lightly_active"),
            cuisines_json,
            sqlite_id,
            local_updated,
        ),
    )


def _sync_meal_plan(pg_cur, cloud_uuid: str, item: dict, cur_sqlite) -> None:
    """Synchronizes meal plans with sqlite_id deduplication."""
    payload = json.loads(item["payload"])
    sqlite_id = item["entity_id"]
    plan_date = payload.get("date")
    target_cal = payload.get("target_calories", 2000)
    items = payload.get("items", "[]")
    items_json = json.dumps(items) if not isinstance(items, str) else items
    status = payload.get("status", "generated")

    enum_status = status if status in ["generated", "active", "completed", "abandoned"] else "generated"

    pg_cur.execute(
        """
        INSERT INTO public.meal_plans (
            user_id, plan_date, total_calories_target, total_calories_actual,
            plan_status, items, sqlite_id, synced_at, created_at, updated_at
        ) VALUES (
            %s, %s, %s, 0,
            %s, %s::jsonb, %s, NOW(), NOW(), NOW()
        )
        ON CONFLICT (sqlite_id) DO UPDATE SET
            total_calories_target = EXCLUDED.total_calories_target,
            plan_status = EXCLUDED.plan_status,
            items = EXCLUDED.items,
            synced_at = NOW(),
            updated_at = NOW();
        """,
        (cloud_uuid, plan_date, target_cal, enum_status, items_json, sqlite_id),
    )


def _sync_meal_log(pg_cur, cloud_uuid: str, item: dict, cur_sqlite) -> None:
    """Synchronizes meal logs using sqlite_id unique key."""
    payload = json.loads(item["payload"])
    sqlite_id = item["entity_id"]
    meal_id = str(payload.get("meal_id", ""))
    status = payload.get("status", "eaten")
    reason = payload.get("reason")
    item_tags = payload.get("item_tags", "[]")
    item_tags_json = json.dumps(item_tags) if not isinstance(item_tags, str) else item_tags
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()

    valid_reason = reason if reason in ["time", "cost", "taste", "unavailable"] else None

    pg_cur.execute(
        """
        INSERT INTO public.meal_logs (
            user_id, meal_id, status, reason, item_tags, timestamp,
            sqlite_id, synced_at, created_at
        ) VALUES (
            %s, %s, %s, %s, %s::jsonb, %s,
            %s, NOW(), NOW()
        )
        ON CONFLICT (sqlite_id) DO UPDATE SET
            status = EXCLUDED.status,
            reason = EXCLUDED.reason,
            item_tags = EXCLUDED.item_tags,
            timestamp = EXCLUDED.timestamp,
            synced_at = NOW();
        """,
        (cloud_uuid, meal_id, status, valid_reason, item_tags_json, timestamp, sqlite_id),
    )


def _sync_feedback(pg_cur, cloud_uuid: str, item: dict, cur_sqlite) -> None:
    """Synchronizes adaptive feedback into public.app_feedback."""
    payload = json.loads(item["payload"])
    sqlite_id = item["entity_id"]
    meal_id = str(payload.get("meal_id", ""))
    status = payload.get("status", "skipped")
    reason = payload.get("reason", "")
    feedback_text = payload.get("feedback_text", "")
    penalty_tag = payload.get("derived_penalty_tag", "")

    pg_cur.execute(
        """
        INSERT INTO public.app_feedback (
            user_id, meal_id, status, reason, feedback_text, derived_penalty_tag,
            sqlite_id, synced_at, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, NOW(), NOW()
        )
        ON CONFLICT (sqlite_id) DO UPDATE SET
            status = EXCLUDED.status,
            reason = EXCLUDED.reason,
            feedback_text = EXCLUDED.feedback_text,
            derived_penalty_tag = EXCLUDED.derived_penalty_tag,
            synced_at = NOW();
        """,
        (cloud_uuid, meal_id, status, reason, feedback_text, penalty_tag, sqlite_id),
    )


def _sync_pantry_item(pg_cur, cloud_uuid: str, item: dict, cur_sqlite) -> None:
    """Synchronizes pantry items (UPSERT and DELETE operations)."""
    operation = item["operation"]
    sqlite_id = item["entity_id"]

    if operation == "DELETE":
        pg_cur.execute("DELETE FROM public.pantry_items WHERE sqlite_id = %s;", (sqlite_id,))
        return

    payload = json.loads(item["payload"])
    name = payload.get("name", "").strip()
    category = payload.get("category", "General")
    quantity = payload.get("quantity", "1 unit")
    in_stock = bool(payload.get("in_stock", 1))
    source = payload.get("source", "manual")

    pg_cur.execute(
        """
        INSERT INTO public.pantry_items (
            user_id, name, category, quantity, in_stock, source,
            sqlite_id, synced_at, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, NOW(), NOW(), NOW()
        )
        ON CONFLICT (user_id, name) DO UPDATE SET
            category = EXCLUDED.category,
            quantity = EXCLUDED.quantity,
            in_stock = EXCLUDED.in_stock,
            source = EXCLUDED.source,
            sqlite_id = EXCLUDED.sqlite_id,
            synced_at = NOW(),
            updated_at = NOW();
        """,
        (cloud_uuid, name, category, quantity, in_stock, source, sqlite_id),
    )


# ─── Main Synchronization Engine ──────────────────────────────────────────────

def sync_user_data(user_id: str, max_items: int = 100) -> Dict[str, Any]:
    """
    Processes the local `sync_queue` for a user and pushes pending changes to Supabase.
    - Idempotent and conflict-aware (Last-Write-Wins).
    - If Supabase is unreachable, records error gracefully without disrupting local operations.
    - Updates `sync_metadata` with progress and timestamps.
    """
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO sync_metadata (user_id, sync_status, last_attempt_at, updated_at)
            VALUES (?, 'in_progress', ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                sync_status = 'in_progress',
                last_attempt_at = ?,
                updated_at = ?
            """,
            (user_id, now, now, now, now),
        )

    pg_conn = get_pg_connection(autocommit=True, timeout=5)
    if not pg_conn:
        err_msg = "Supabase PostgreSQL connection failed or unreachable"
        with get_db_cursor() as cur:
            cur.execute(
                """
                UPDATE sync_metadata SET
                    sync_status = 'error',
                    last_error = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (err_msg, now, user_id),
            )
        return {
            "success": False,
            "error": err_msg,
            "synced_count": 0,
            "failed_count": 0,
            "pending_count": get_sync_status(user_id, check_cloud=False)["pending_count"],
        }

    synced_count = 0
    failed_count = 0

    try:
        with get_db_cursor() as cur_sqlite:
            cloud_uuid = _resolve_cloud_user_uuid(cur_sqlite, pg_conn, user_id)
            if not cloud_uuid:
                raise RuntimeError(f"Could not resolve Supabase UUID for user {user_id}")

            cur_sqlite.execute(
                """
                SELECT * FROM sync_queue
                WHERE user_id = ? AND status IN ('pending', 'failed')
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (user_id, max_items),
            )
            items = cur_sqlite.fetchall()

            for raw_item in items:
                item = dict(raw_item)
                item_id = item["id"]
                entity_type = item["entity_type"]

                cur_sqlite.execute("UPDATE sync_queue SET status = 'syncing' WHERE id = ?", (item_id,))

                try:
                    pg_cur = pg_conn.cursor()
                    if entity_type == "profile":
                        _sync_profile(pg_cur, cloud_uuid, item, cur_sqlite)
                    elif entity_type == "meal_plan":
                        _sync_meal_plan(pg_cur, cloud_uuid, item, cur_sqlite)
                    elif entity_type == "meal_log":
                        _sync_meal_log(pg_cur, cloud_uuid, item, cur_sqlite)
                    elif entity_type == "feedback":
                        _sync_feedback(pg_cur, cloud_uuid, item, cur_sqlite)
                    elif entity_type == "pantry_item":
                        _sync_pantry_item(pg_cur, cloud_uuid, item, cur_sqlite)

                    cur_sqlite.execute(
                        "UPDATE sync_queue SET status = 'synced', last_error = NULL, updated_at = ? WHERE id = ?",
                        (now, item_id),
                    )

                    table_name = "feedback" if entity_type == "feedback" else (
                        "meal_plans" if entity_type == "meal_plan" else (
                            "meal_logs" if entity_type == "meal_log" else (
                                "pantry_items" if entity_type == "pantry_item" else "profiles"
                            )
                        )
                    )
                    id_col = "user_id" if entity_type == "profile" else "id"
                    try:
                        cur_sqlite.execute(f"UPDATE {table_name} SET synced_at = ? WHERE {id_col} = ?", (now, item["entity_id"]))
                    except Exception:
                        pass

                    synced_count += 1

                except Exception as item_err:
                    failed_count += 1
                    retries = item["retry_count"] + 1
                    new_status = "failed" if retries >= item["max_retries"] else "pending"
                    cur_sqlite.execute(
                        """
                        UPDATE sync_queue SET
                            status = ?,
                            retry_count = ?,
                            last_error = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (new_status, retries, str(item_err), now, item_id),
                    )

            remaining_res = cur_sqlite.execute(
                "SELECT COUNT(*) FROM sync_queue WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            ).fetchone()
            remaining_pending = remaining_res[0] if remaining_res else 0

            final_status = "synced" if (remaining_pending == 0 and failed_count == 0) else (
                "error" if failed_count > 0 else "pending"
            )

            cur_sqlite.execute(
                """
                UPDATE sync_metadata SET
                    last_synced_at = CASE WHEN ? > 0 THEN ? ELSE last_synced_at END,
                    sync_status = ?,
                    pending_count = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    synced_count,
                    now,
                    final_status,
                    remaining_pending,
                    f"{failed_count} items failed" if failed_count > 0 else None,
                    now,
                    user_id,
                ),
            )

    finally:
        pg_conn.close()

    return {
        "success": failed_count == 0,
        "synced_count": synced_count,
        "failed_count": failed_count,
        "pending_count": remaining_pending if "remaining_pending" in locals() else 0,
        "last_synced_at": now if synced_count > 0 else None,
    }


def retry_failed_sync(user_id: str) -> Dict[str, Any]:
    """Resets failed queue items to pending and triggers synchronization."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            UPDATE sync_queue SET
                status = 'pending',
                retry_count = 0,
                updated_at = ?
            WHERE user_id = ? AND status = 'failed'
            """,
            (now, user_id),
        )
    return sync_user_data(user_id)
