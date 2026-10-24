"""
DietSense — Meal Logs & Adherence Routes
Captures meal outcomes (eaten vs skipped with reason), verifies user ownership,
and provides real calculated adherence analytics for Recharts visualizations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from app.core.dependencies import get_current_user
from routes.feedback import USER_MEAL_LOGS

router = APIRouter(tags=["Meal Logs & Analytics"])

ALLOWED_STATUSES = {"eaten", "skipped"}
ALLOWED_SKIP_REASONS = {"time", "cost", "taste", "unavailable"}


@router.get("/meal-logs")
@router.get("/meal_logs")
async def get_meal_logs(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all meal logs for the verified authenticated user.
    """
    user_id = user["id"]
    return USER_MEAL_LOGS.get(user_id, [])


@router.post("/meal-logs", status_code=status.HTTP_201_CREATED)
@router.post("/meal_logs", status_code=status.HTTP_201_CREATED)
async def create_meal_log(
    log_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Record meal outcome (eaten or skipped with reason).
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

    if user_id not in USER_MEAL_LOGS:
        USER_MEAL_LOGS[user_id] = []

    now = datetime.now(timezone.utc).isoformat()
    log_entry = {
        "id": f"log_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "meal_id": log_data.get("meal_id"),
        "status": raw_status,
        "reason": reason if raw_status == "skipped" else None,
        "item_tags": log_data.get("item_tags", []),
        "timestamp": log_data.get("timestamp") or now,
        "created_at": now,
    }

    USER_MEAL_LOGS[user_id].append(log_entry)
    return {"status": "success", "logged": log_entry}


@router.get("/analytics")
@router.get("/meal-logs/analytics")
async def get_adherence_analytics(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Calculates real adherence and trend analytics strictly from the user's logged meals.
    No fabricated data. Used by frontend Recharts components.
    """
    user_id = user["id"]
    logs = USER_MEAL_LOGS.get(user_id, [])

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
    daily_groups: Dict[str, Dict[str, int]] = {}
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
