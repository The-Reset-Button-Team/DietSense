"""
DietSense - User & Profile Routes Stub
Handles user onboarding, profile retrieval, and settings updates.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/users", tags=["Users"])


from app.core.dependencies import get_current_user

# In-memory storage for user profiles keyed by user_id
USER_PROFILES: Dict[str, Dict[str, Any]] = {}

@router.get("/profile")
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve current authenticated user's profile and nutritional targets.
    """
    user_id = user["id"]
    if user_id in USER_PROFILES:
        return USER_PROFILES[user_id]
    return {
        "id": user_id,
        "email": user.get("email"),
        "full_name": user.get("user_metadata", {}).get("full_name", "User"),
        "dietary_pref": "vegetarian",
        "allergies": [],
        "target_calories": 2000,
        "budget_per_meal": 100,
        "prep_time_limit": 30,
    }

@router.post("/profile")
async def update_user_profile(
    profile_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create or update user onboarding profile (age, diet, budget, prep-time).
    """
    user_id = user["id"]
    profile = {
        **USER_PROFILES.get(user_id, {}),
        **profile_data,
        "id": user_id,
        "email": user.get("email"),
    }
    USER_PROFILES[user_id] = profile
    return profile
