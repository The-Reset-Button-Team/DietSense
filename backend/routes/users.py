"""
DietSense — User & Profile Routes
Handles user onboarding, profile retrieval, and settings updates in local SQLite.
Supports GET /profile, PUT /profile, GET /users/profile, and POST /users/profile.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import json
import uuid
from datetime import datetime, timezone

from app.core.dependencies import get_current_user
from db.database import get_db_cursor

router = APIRouter(tags=["Users & Profile"])


def _row_to_profile(row: Any) -> Dict[str, Any]:
    """Converts a SQLite profile row into the application profile dictionary."""
    allergies = []
    if row["allergies"]:
        try:
            allergies = json.loads(row["allergies"])
        except Exception:
            allergies = [a.strip() for a in str(row["allergies"]).split(",") if a.strip()]

    cuisines = ["indian"]
    if "preferred_cuisines" in row.keys() and row["preferred_cuisines"]:
        try:
            cuisines = json.loads(row["preferred_cuisines"])
        except Exception:
            cuisines = [c.strip() for c in str(row["preferred_cuisines"]).split(",") if c.strip()]

    return {
        "id": row["user_id"],
        "user_id": row["user_id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "dietary_pref": row["dietary_pref"],
        "allergies": allergies,
        "target_calories": int(row["target_calories"]),
        "budget_per_meal": float(row["budget_per_meal"]),
        "prep_time_limit": int(row["prep_time_limit"]),
        "is_solo_cook": bool(row["is_solo_cook"]),
        "active_meal_frequency": row["active_meal_frequency"],
        "age": int(row["age"]),
        "gender": row["gender"],
        "height_cm": float(row["height_cm"]),
        "weight_kg": float(row["weight_kg"]),
        "goal": row["goal"],
        "activity_level": row["activity_level"],
        "preferred_cuisines": cuisines,
        "updated_at": row["updated_at"],
    }


@router.get("/profile")
@router.get("/users/profile")
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve current authenticated user's profile and nutritional targets from SQLite.
    Never trusts client-provided user IDs.
    """
    user_id = user["id"]
    email = user.get("email") or f"{user_id}@dietsense.local"
    full_name = user.get("user_metadata", {}).get("full_name") or email.split("@")[0]
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return _row_to_profile(row)

        # Baseline profile creation if not yet initialized
        prof_id = f"prof_{uuid.uuid4().hex[:12]}"
        cur.execute(
            """
            INSERT OR IGNORE INTO profiles (
                id, user_id, email, full_name, dietary_pref, allergies,
                target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                active_meal_frequency, age, gender, height_cm, weight_kg,
                goal, activity_level, preferred_cuisines, updated_at
            ) VALUES (
                ?, ?, ?, ?, 'vegetarian', '[]',
                2000, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', '["indian"]', ?
            )
            """,
            (prof_id, user_id, email, full_name, now),
        )
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        new_row = cur.fetchone()
        if new_row:
            return _row_to_profile(new_row)

    return {
        "id": user_id,
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
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
    Persists directly to SQLite database.
    """
    user_id = user["id"]
    email = user.get("email") or f"{user_id}@dietsense.local"
    full_name = profile_data.get("full_name") or user.get("user_metadata", {}).get("full_name") or email.split("@")[0]
    now = datetime.now(timezone.utc).isoformat()

    allergies_raw = profile_data.get("allergies", [])
    allergies_json = json.dumps(allergies_raw if isinstance(allergies_raw, list) else [allergies_raw])

    cuisines_raw = profile_data.get("preferred_cuisines", ["indian"])
    cuisines_json = json.dumps(cuisines_raw if isinstance(cuisines_raw, list) else [cuisines_raw])

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        existing = cur.fetchone()

        if existing:
            dietary_pref = profile_data.get("dietary_pref", existing["dietary_pref"])
            allergies = allergies_json if "allergies" in profile_data else existing["allergies"]
            target_calories = profile_data.get("target_calories", existing["target_calories"])
            budget_per_meal = profile_data.get("budget_per_meal", existing["budget_per_meal"])
            prep_time_limit = profile_data.get("prep_time_limit", existing["prep_time_limit"])
            is_solo_cook = 1 if profile_data.get("is_solo_cook", existing["is_solo_cook"]) else 0
            active_meal_frequency = profile_data.get("active_meal_frequency", existing["active_meal_frequency"])
            age = profile_data.get("age", existing["age"])
            gender = profile_data.get("gender", existing["gender"])
            height_cm = profile_data.get("height_cm", existing["height_cm"])
            weight_kg = profile_data.get("weight_kg", existing["weight_kg"])
            goal = profile_data.get("goal", existing["goal"])
            activity_level = profile_data.get("activity_level", existing["activity_level"])
            preferred_cuisines = cuisines_json if "preferred_cuisines" in profile_data else existing["preferred_cuisines"]

            cur.execute(
                """
                UPDATE profiles SET
                    full_name = ?,
                    dietary_pref = ?,
                    allergies = ?,
                    target_calories = ?,
                    budget_per_meal = ?,
                    prep_time_limit = ?,
                    is_solo_cook = ?,
                    active_meal_frequency = ?,
                    age = ?,
                    gender = ?,
                    height_cm = ?,
                    weight_kg = ?,
                    goal = ?,
                    activity_level = ?,
                    preferred_cuisines = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    full_name,
                    dietary_pref,
                    allergies,
                    target_calories,
                    budget_per_meal,
                    prep_time_limit,
                    is_solo_cook,
                    active_meal_frequency,
                    age,
                    gender,
                    height_cm,
                    weight_kg,
                    goal,
                    activity_level,
                    preferred_cuisines,
                    now,
                    user_id,
                ),
            )
        else:
            prof_id = f"prof_{uuid.uuid4().hex[:12]}"
            cur.execute(
                """
                INSERT INTO profiles (
                    id, user_id, email, full_name, dietary_pref, allergies,
                    target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                    active_meal_frequency, age, gender, height_cm, weight_kg,
                    goal, activity_level, preferred_cuisines, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    prof_id,
                    user_id,
                    email,
                    full_name,
                    profile_data.get("dietary_pref", "vegetarian"),
                    allergies_json,
                    profile_data.get("target_calories", 2000),
                    profile_data.get("budget_per_meal", 100.0),
                    profile_data.get("prep_time_limit", 30),
                    1 if profile_data.get("is_solo_cook", True) else 0,
                    profile_data.get("active_meal_frequency", "3_meals"),
                    profile_data.get("age", 26),
                    profile_data.get("gender", "male"),
                    profile_data.get("height_cm", 175.0),
                    profile_data.get("weight_kg", 75.0),
                    profile_data.get("goal", "lose_weight"),
                    profile_data.get("activity_level", "lightly_active"),
                    cuisines_json,
                    now,
                ),
            )

        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        updated_row = cur.fetchone()
        return _row_to_profile(updated_row)
