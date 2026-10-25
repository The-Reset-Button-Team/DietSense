"""
DietSense — Meal Logs & Adherence Routes
Captures meal outcomes (eaten vs skipped with reason), verifies user ownership,
and provides real calculated adherence analytics for Recharts visualizations.
Persists data to local SQLite database.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import uuid

from app.core.dependencies import get_current_user
from db.database import get_db_cursor

router = APIRouter(tags=["Meal Logs & Analytics"])

ALLOWED_STATUSES = {"eaten", "skipped"}
ALLOWED_SKIP_REASONS = {"time", "cost", "taste", "unavailable"}


def _row_to_log(row: Any) -> Dict[str, Any]:
    item_tags = []
    if row["item_tags"]:
        try:
            item_tags = json.loads(row["item_tags"])
        except Exception:
            item_tags = [t.strip() for t in str(row["item_tags"]).split(",") if t.strip()]
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "meal_id": row["meal_id"],
        "status": row["status"],
        "reason": row["reason"],
        "item_tags": item_tags,
        "timestamp": row["timestamp"],
        "created_at": row["created_at"],
    }


def get_user_meal_logs(user_id: str) -> List[Dict[str, Any]]:
    """Helper to load all meal logs for a specific user from SQLite."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_logs WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,),
        )
        return [_row_to_log(r) for r in cur.fetchall()]


@router.get("/meal-logs")
@router.get("/meal_logs")
async def get_meal_logs(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all meal logs for the verified authenticated user from SQLite.
    """
    user_id = user["id"]
    return get_user_meal_logs(user_id)


@router.post("/meal-logs", status_code=status.HTTP_201_CREATED)
@router.post("/meal_logs", status_code=status.HTTP_201_CREATED)
async def create_meal_log(
    log_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Record meal outcome (eaten or skipped with reason) into SQLite.
    Validates skip reason against: 'time', 'cost', 'taste', 'unavailable'.
    Persisted securely under user_id derived exclusively from JWT.
    """
    user_id = user["id"]

    raw_status = str(log_data.get("status") or "").strip().lower()
    if raw_status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{raw_status}'. Must be 'eaten' or 'skipped'.",
        )

    reason = log_data.get("reason")
    if reason is not None:
        reason = str(reason).strip().lower()
        if reason and reason not in ALLOWED_SKIP_REASONS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid skip reason '{reason}'. Allowed values are: {sorted(ALLOWED_SKIP_REASONS)}.",
            )

    log_id = f"log_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    meal_id = str(log_data.get("meal_id", ""))
    reason_val = reason if raw_status == "skipped" else None
    item_tags_json = json.dumps(log_data.get("item_tags", []))
    timestamp = log_data.get("timestamp") or now

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO meal_logs (id, user_id, meal_id, status, reason, item_tags, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, user_id, meal_id, raw_status, reason_val, item_tags_json, timestamp, now),
        )
        cur.execute("SELECT * FROM meal_logs WHERE id = ?", (log_id,))
        created_row = cur.fetchone()

    log_entry = _row_to_log(created_row)
    return {"status": "success", "logged": log_entry}


@router.get("/analytics")
@router.get("/meal-logs/analytics")
async def get_adherence_analytics(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Calculates real adherence and trend analytics strictly from the user's logged meals in SQLite.
    No fabricated data. Used by frontend Recharts components.
    """
    user_id = user["id"]
    logs = get_user_meal_logs(user_id)

    total = len(logs)
    if total == 0:
        return {
            "total_logged": 0,
            "eaten_count": 0,
            "skipped_count": 0,
            "adherence_rate_pct": 0.0,
            "skip_reasons": {r: 0 for r in ALLOWED_SKIP_REASONS},
            "daily_trends": [],
            "has_data": False,
        }

    eaten = sum(1 for l in logs if l.get("status") == "eaten")
    skipped = sum(1 for l in logs if l.get("status") == "skipped")
    adherence_pct = round((eaten / total) * 100.0, 1)

    reason_counts = {r: 0 for r in ALLOWED_SKIP_REASONS}
    for l in logs:
        r = l.get("reason")
        if r in reason_counts:
            reason_counts[r] += 1

    # Group daily trends by date string
    daily_groups: Dict[str, Dict[str, Any]] = {}
    for l in logs:
        ts = l.get("timestamp") or l.get("created_at") or datetime.now(timezone.utc).isoformat()
        date_str = ts.split("T")[0]
        if date_str not in daily_groups:
            daily_groups[date_str] = {"date": date_str, "eaten": 0, "skipped": 0}
        if l.get("status") == "eaten":
            daily_groups[date_str]["eaten"] += 1
        elif l.get("status") == "skipped":
            daily_groups[date_str]["skipped"] += 1

    daily_trends = sorted(daily_groups.values(), key=lambda x: x["date"])

    return {
        "total_logged": total,
        "eaten_count": eaten,
        "skipped_count": skipped,
        "adherence_rate_pct": adherence_pct,
        "skip_reasons": reason_counts,
        "daily_trends": daily_trends,
        "has_data": True,
    }
