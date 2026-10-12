"""
DietSense - Feedback & Meal Logs Routes Stub
Captures meal outcomes (eaten vs skipped) and trigger adaptive model reweighting.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/feedback", tags=["Feedback"])


from fastapi import Depends
from app.core.dependencies import get_current_user

USER_MEAL_LOGS: Dict[str, list] = {}

@router.post("/")
async def log_meal_feedback(
    feedback_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Log eaten/skipped status, skip reason, and tie securely to the verified user.
    """
    user_id = user["id"]
    if user_id not in USER_MEAL_LOGS:
        USER_MEAL_LOGS[user_id] = []

    log_entry = {
        **feedback_data,
        "user_id": user_id,
    }
    USER_MEAL_LOGS[user_id].append(log_entry)
    return {"status": "success", "logged": log_entry}

@router.get("/")
async def get_meal_feedback(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve meal logs and feedback for the verified user only.
    """
    user_id = user["id"]
    return USER_MEAL_LOGS.get(user_id, [])
