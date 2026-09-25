"""
DietSense - User & Profile Routes Stub
Handles user onboarding, profile retrieval, and settings updates.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile")
async def get_user_profile():
    """
    Retrieve current authenticated user's profile and nutritional targets.
    """
    # TODO: Fetch user profile from Supabase/PostgreSQL
    pass


@router.post("/profile")
async def update_user_profile(profile_data: Dict[str, Any]):
    """
    Create or update user onboarding profile (age, diet, budget, prep-time).
    """
    # TODO: Save updated profile attributes
    pass
