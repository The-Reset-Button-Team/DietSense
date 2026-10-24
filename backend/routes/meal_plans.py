"""
DietSense — Meal Plans Routes
Allows authenticated users to generate, persist, and retrieve daily/weekly meal plans.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from app.core.dependencies import get_current_user

router = APIRouter(tags=["Meal Plans"])

# In-memory user-isolated meal plans storage (keyed by user_id)
USER_MEAL_PLANS: Dict[str, List[Dict[str, Any]]] = {}


@router.get("/meal-plans")
@router.get("/meal_plans")
async def get_meal_plans(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all meal plans created by the authenticated user.
    """
    user_id = user["id"]
    return USER_MEAL_PLANS.get(user_id, [])


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
    if user_id not in USER_MEAL_PLANS:
        USER_MEAL_PLANS[user_id] = []

    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()

    new_plan = {
        "id": plan_id,
        "user_id": user_id,
        "date": plan_data.get("date", now.strftime("%Y-%m-%d")),
        "target_calories": plan_data.get("target_calories", 2000),
        "items": plan_data.get("items", []),
        "status": plan_data.get("status", "generated"),
        "created_at": created_at,
    }

    USER_MEAL_PLANS[user_id].append(new_plan)
    return new_plan


@router.get("/meal-plans/{plan_id}")
async def get_meal_plan_by_id(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve a specific meal plan by ID, verifying user ownership.
    """
    user_id = user["id"]
    plans = USER_MEAL_PLANS.get(user_id, [])
    for p in plans:
        if p["id"] == plan_id:
            return p
    raise HTTPException(status_code=404, detail="Meal plan not found or access denied")
