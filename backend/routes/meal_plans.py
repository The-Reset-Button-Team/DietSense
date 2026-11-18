"""
DietSense — Meal Plans Routes
Allows authenticated users to generate, persist, and retrieve daily/weekly meal plans.
Data is persisted to local SQLite database with strict user ownership enforcement.
Mutations are enqueued into the local sync_queue for cloud synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json
import uuid

from app.core.dependencies import get_current_user
from db.database import get_db_cursor
from app.core.sync_service import enqueue_sync_operation

router = APIRouter(tags=["Meal Plans"])

VALID_PLAN_STATUSES = {"generated", "accepted", "completed"}


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
        "updated_at": row["updated_at"] if "updated_at" in row.keys() and row["updated_at"] else row["created_at"],
    }


@router.get("/meal-plans")
@router.get("/meal_plans")
async def get_meal_plans(
    date: Optional[str] = Query(None, description="Filter plans by exact date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Start date for range filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for range filter (YYYY-MM-DD)"),
    plan_status: Optional[str] = Query(None, alias="status", description="Filter by status (generated, accepted, completed)"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve meal plans created by the authenticated user with optional date and status filters.
    Enforces strict user data isolation.
    """
    user_id = user["id"]
    query = "SELECT * FROM meal_plans WHERE user_id = ?"
    params: List[Any] = [user_id]

    if date:
        query += " AND date = ?"
        params.append(date)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if plan_status:
        query += " AND status = ?"
        params.append(plan_status)

    query += " ORDER BY date DESC, created_at DESC"

    with get_db_cursor() as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return [_row_to_plan(r) for r in rows]


@router.get("/meal-plans/weekly")
@router.get("/meal_plans/weekly")
async def get_weekly_meal_plans(
    start_date: Optional[str] = Query(None, description="Start date of the week (YYYY-MM-DD)"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve meal plans for a 7-day week starting from start_date (or current Monday).
    Returns an array of 7 day slots with either the plan or null if not planned yet.
    """
    user_id = user["id"]

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format, expected YYYY-MM-DD")
    else:
        now = datetime.now(timezone.utc)
        # Default to Monday of current week
        start_dt = now - timedelta(days=now.weekday())

    dates = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    end_date_str = dates[-1]
    start_date_str = dates[0]

    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM meal_plans
            WHERE user_id = ? AND date >= ? AND date <= ?
            ORDER BY date ASC, created_at DESC
            """,
            (user_id, start_date_str, end_date_str),
        )
        rows = cur.fetchall()

    plans_by_date: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        d = r["date"]
        if d not in plans_by_date:  # Keep newest per date
            plans_by_date[d] = _row_to_plan(r)

    weekly_schedule = []
    for d in dates:
        weekly_schedule.append({
            "date": d,
            "plan": plans_by_date.get(d, None),
        })

    return {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "days": weekly_schedule,
    }


@router.post("/meal-plans", status_code=status.HTTP_201_CREATED)
@router.post("/meal_plans", status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    plan_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create and persist a new meal plan composed of recommended recipes/meals.
    Guarantees user ownership (user_id derived exclusively from JWT).
    Enqueues mutation to local sync_queue.
    """
    user_id = user["id"]
    custom_id = plan_data.get("id") or plan_data.get("plan_id")
    plan_id = custom_id if custom_id else f"plan_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    plan_date = plan_data.get("date", now.strftime("%Y-%m-%d"))
    target_cal = int(plan_data.get("target_calories", 2000))
    items_json = json.dumps(plan_data.get("items", []))
    plan_status = plan_data.get("status", "generated")

    if plan_status not in VALID_PLAN_STATUSES:
        plan_status = "generated"

    with get_db_cursor() as cur:
        # Check if updating an existing plan by ID
        cur.execute("SELECT * FROM meal_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                UPDATE meal_plans
                SET date = ?, target_calories = ?, items = ?, status = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (plan_date, target_cal, items_json, plan_status, created_at, plan_id, user_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO meal_plans (id, user_id, date, target_calories, items, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (plan_id, user_id, plan_date, target_cal, items_json, plan_status, created_at, created_at),
            )

        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        row = cur.fetchone()

    # Enqueue mutation for cloud synchronization
    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="UPSERT",
        payload={
            "id": plan_id,
            "user_id": user_id,
            "date": plan_date,
            "target_calories": target_cal,
            "items": plan_data.get("items", []),
            "status": plan_status,
            "created_at": created_at,
            "updated_at": created_at,
        },
    )

    return _row_to_plan(row)


@router.get("/meal-plans/{plan_id}")
@router.get("/meal_plans/{plan_id}")
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


@router.patch("/meal-plans/{plan_id}/status")
@router.patch("/meal_plans/{plan_id}/status")
@router.put("/meal-plans/{plan_id}/status")
@router.put("/meal_plans/{plan_id}/status")
async def update_meal_plan_status(
    plan_id: str,
    status_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update the status of an existing meal plan (e.g. generated -> accepted -> completed).
    Verifies strict user ownership before mutation.
    """
    user_id = user["id"]
    new_status = status_data.get("status")

    if not new_status or new_status not in VALID_PLAN_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed values: {sorted(list(VALID_PLAN_STATUSES))}",
        )

    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM meal_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meal plan not found or access denied")

        cur.execute(
            "UPDATE meal_plans SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (new_status, now, plan_id, user_id),
        )
        cur.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
        updated_row = cur.fetchone()

    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="UPSERT",
        payload=_row_to_plan(updated_row),
    )

    return _row_to_plan(updated_row)


@router.delete("/meal-plans/{plan_id}")
@router.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a meal plan belonging to the authenticated user.
    Enforces user data isolation.
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

        cur.execute("DELETE FROM meal_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))

    enqueue_sync_operation(
        user_id=user_id,
        entity_type="meal_plan",
        entity_id=plan_id,
        operation="DELETE",
        payload={"id": plan_id},
    )

    return {"status": "success", "message": f"Meal plan {plan_id} deleted"}
