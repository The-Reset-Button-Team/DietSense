"""
DietSense — Meal Plans Routes
Allows authenticated users to generate, persist, and retrieve daily/weekly meal plans.
Data is persisted to local SQLite database with strict user ownership enforcement.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import uuid

from app.core.dependencies import get_current_user
from db.database import get_db_cursor

router = APIRouter(tags=["Meal Plans"])


def _row_to_plan(row: Any) -> Dict[str, Any]:
    """Converts a SQLite meal_plan row to dictionary."""
    items = []
    if row["items"]:
        try:
            items = json.loads(row["items"])
        except Exception:
            items = []
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "date": row["date"],
        "target_calories": int(row["target_calories"]),
        "items": items,
        "status": row["status"],
        "created_at": row["created_at"],
    }


@router.get("/meal-plans")
@router.get("/meal_plans")
async def get_meal_plans(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all meal plans created by the authenticated user.
    Enforces user data isolation.
    """
    user_id = user["id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        return [_row_to_plan(r) for r in rows]


@router.post("/meal-plans", status_code=status.HTTP_201_CREATED)
@router.post("/meal_plans", status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    plan_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create and persist a new meal plan composed of recommended recipes/meals.
    Guarantees user ownership (user_id derived exclusively from JWT).
    """
    user_id = user["id"]
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    plan_date = plan_data.get("date", now.strftime("%Y-%m-%d"))
    target_cal = int(plan_data.get("target_calories", 2000))
    items_json = json.dumps(plan_data.get("items", []))
    plan_status = plan_data.get("status", "generated")

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO meal_plans (id, user_id, date, target_calories, items, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (plan_id, user_id, plan_date, target_cal, items_json, plan_status, created_at),
        )
        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        row = cur.fetchone()
        return _row_to_plan(row)


@router.get("/meal-plans/{plan_id}")
async def get_meal_plan_by_id(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve a specific meal plan by ID, verifying user ownership.
    Prevents cross-user data leakage.
    """
    user_id = user["id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meal plan not found or access denied")
        return _row_to_plan(row)
