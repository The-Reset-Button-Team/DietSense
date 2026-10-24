"""
DietSense - User & Profile Routes Stub
Handles user onboarding, profile retrieval, and settings updates.
Supports GET /profile, PUT /profile, GET /users/profile, and POST /users/profile.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.core.dependencies import get_current_user

router = APIRouter(tags=["Users & Profile"])

# In-memory storage for user profiles keyed by user_id
USER_PROFILES: Dict[str, Dict[str, Any]] = {}


@router.get("/profile")
@router.get("/users/profile")
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
        "is_solo_cook": True,
        "active_meal_frequency": "3_meals",
    }


@router.put("/profile")
@router.post("/profile")
@router.post("/users/profile")
async def update_user_profile(
    profile_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create or update user onboarding profile (diet, allergies, calories, budget, prep-time).
    """
    user_id = user["id"]
    existing = USER_PROFILES.get(user_id, {})
    profile = {
        **existing,
        **profile_data,
        "id": user_id,
        "email": user.get("email"),
    }
    USER_PROFILES[user_id] = profile
    return profile
