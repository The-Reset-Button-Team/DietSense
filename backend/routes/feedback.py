"""
DietSense — Feedback & Meal Logs Routes
Captures meal outcomes (eaten vs skipped) and feedback tied securely to verified users.
Persists records in local SQLite database and enqueues to sync_queue.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import uuid

from app.core.dependencies import get_current_user
from db.database import get_db_cursor
from ml.adaptive.reweight import REASON_TAG_MAP
from app.core.sync_service import enqueue_sync_operation

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _row_to_feedback(row: Any) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "meal_id": row["meal_id"],
        "status": row["status"],
        "reason": row["reason"],
        "feedback_text": row["feedback_text"],
        "derived_penalty_tag": row["derived_penalty_tag"],
        "created_at": row["created_at"],
    }


@router.post("/")
async def log_meal_feedback(
    feedback_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Log eaten/skipped status, skip reason, and tie securely to the verified user in SQLite.
    Also synchronizes into meal_logs so that ML adaptive penalties and analytics reflect it.
    Enqueues mutations for cloud sync.
    """
    user_id = user["id"]
    fb_id = f"fb_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    meal_id = str(feedback_data.get("meal_id", ""))
    status_val = str(feedback_data.get("status", "eaten")).strip().lower()
    reason_val = feedback_data.get("reason")
    if reason_val:
        reason_val = str(reason_val).strip().lower()

    derived_tag = REASON_TAG_MAP.get(reason_val) if reason_val else None
    feedback_text = feedback_data.get("feedback_text") or feedback_data.get("comment")

    with get_db_cursor() as cur:
        # Insert into feedback table
        cur.execute(
            """
            INSERT INTO feedback (id, user_id, meal_id, status, reason, feedback_text, derived_penalty_tag, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fb_id, user_id, meal_id, status_val, reason_val, feedback_text, derived_tag, now, now),
        )

        log_id = None
        # Synchronize into meal_logs if status is valid
        if status_val in ("eaten", "skipped"):
            log_id = f"log_{uuid.uuid4().hex[:12]}"
            tags = [derived_tag] if derived_tag else []
            tags_json = json.dumps(tags)
            cur.execute(
                """
                INSERT INTO meal_logs (id, user_id, meal_id, status, reason, item_tags, timestamp, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, user_id, meal_id, status_val, reason_val, tags_json, now, now, now),
            )

        cur.execute("SELECT * FROM feedback WHERE id = ?", (fb_id,))
        row = cur.fetchone()

    # Enqueue feedback for sync
    enqueue_sync_operation(
        user_id=user_id,
        entity_type="feedback",
        entity_id=fb_id,
        operation="UPSERT",
        payload={
            "id": fb_id,
            "user_id": user_id,
            "meal_id": meal_id,
            "status": status_val,
            "reason": reason_val,
            "feedback_text": feedback_text,
            "derived_penalty_tag": derived_tag,
            "created_at": now,
            "updated_at": now,
        },
    )

    if log_id:
        enqueue_sync_operation(
            user_id=user_id,
            entity_type="meal_log",
            entity_id=log_id,
            operation="UPSERT",
            payload={
                "id": log_id,
                "user_id": user_id,
                "meal_id": meal_id,
                "status": status_val,
                "reason": reason_val,
                "item_tags": [derived_tag] if derived_tag else [],
                "timestamp": now,
                "created_at": now,
                "updated_at": now,
            },
        )

    log_entry = _row_to_feedback(row)
    return {"status": "success", "logged": log_entry}


@router.get("/")
async def get_meal_feedback(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve meal logs and feedback for the verified user only from SQLite.
    Guarantees user isolation.
    """
    user_id = user["id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        return [_row_to_feedback(r) for r in rows]
