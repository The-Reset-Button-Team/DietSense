"""
DietSense — Authentication & Profile Routes
Local database-backed authentication using bcrypt password hashing,
session cookies, and JWT verification. No Supabase dependency.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    UserUpdateRequest,
)
from app.core.config import settings
from app.core.security import (
    normalize_email,
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.dependencies import get_current_user
from db.database import get_db_cursor, get_connection

router = APIRouter()


def _set_auth_cookie(response: Response, token: str) -> None:
    """Sets a secure HttpOnly session cookie."""
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.session_cookie_secure if settings.is_production else False,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def _calculate_target_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
    goal: str,
) -> int:
    """Calculates daily target calories based on biometrics and goal."""
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "male" else -161)
    act_mult = 1.375 if activity_level == "lightly_active" else (
        1.2 if activity_level == "sedentary" else (
            1.55 if activity_level == "moderately_active" else (
                1.725 if activity_level == "very_active" else 1.9
            )
        )
    )
    tdee = bmr * act_mult
    if goal == "lose_weight":
        target = tdee - 400
    elif goal == "gain_weight":
        target = tdee + 300
    else:
        target = tdee
    return round(target)


@router.post("/register", response_model=UserProfileResponse)
async def register(req: UserRegisterRequest, response: Response):
    """
    Registers a new user with email and password into local SQLite.
    Validates email uniqueness, hashes password with bcrypt, initializes profile,
    and returns verified session credentials.
    """
    email = normalize_email(req.email)
    now = datetime.now(timezone.utc).isoformat()
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(req.password)

    target_cal = _calculate_target_calories(
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        age=req.age,
        gender=req.gender.value,
        activity_level=req.activity_level.value,
        goal=req.goal.value,
    )

    with get_db_cursor() as cur:
        # Check if email is already registered
        cur.execute("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Insert user
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?)
            """,
            (user_id, email, hashed_pw, req.full_name, now, now),
        )

        # Insert profile
        cur.execute(
            """
            INSERT INTO profiles (
                id, user_id, email, full_name, dietary_pref, allergies,
                target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                active_meal_frequency, age, gender, height_cm, weight_kg,
                goal, activity_level, updated_at
            ) VALUES (
                ?, ?, ?, ?, 'vegetarian', '[]',
                ?, 100.0, 30, 1,
                '3_meals', ?, ?, ?, ?,
                ?, ?, ?
            )
            """,
            (
                f"prof_{uuid.uuid4().hex[:12]}",
                user_id,
                email,
                req.full_name,
                target_cal,
                req.age,
                req.gender.value,
                req.height_cm,
                req.weight_kg,
                req.goal.value,
                req.activity_level.value,
                now,
            ),
        )

    token = create_access_token(user_id=user_id, email=email, full_name=req.full_name)
    _set_auth_cookie(response, token)

    return UserProfileResponse(
        id=user_id,
        email=email,
        full_name=req.full_name,
        age=req.age,
        gender=req.gender.value,
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        goal=req.goal.value,
        activity_level=req.activity_level.value,
        daily_calorie_target=target_cal,
        is_solo_cook=True,
        active_meal_frequency="3_meals",
        token=token,
    )


@router.post("/login", response_model=UserProfileResponse)
async def login(req: UserLoginRequest, response: Response):
    """
    Authenticates a user using email and password against local SQLite.
    Verifies bcrypt hash, sets HttpOnly cookie, and returns user profile + token.
    """
    email = normalize_email(req.email)
    with get_db_cursor() as cur:
        cur.execute("SELECT id, email, password_hash, full_name FROM users WHERE email = ? COLLATE NOCASE", (email,))
        user_row = cur.fetchone()

        if not user_row or not verify_password(req.password, user_row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user_id = user_row["id"]
        full_name = user_row["full_name"] or email.split("@")[0]

        # Fetch profile
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        prof = cur.fetchone()

        if not prof:
            # Create default profile if missing
            now = datetime.now(timezone.utc).isoformat()
            cur.execute(
                """
                INSERT INTO profiles (
                    id, user_id, email, full_name, dietary_pref, allergies,
                    target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                    active_meal_frequency, age, gender, height_cm, weight_kg,
                    goal, activity_level, updated_at
                ) VALUES (
                    ?, ?, ?, ?, 'vegetarian', '[]',
                    1850, 100.0, 30, 1,
                    '3_meals', 26, 'male', 175.0, 75.0,
                    'lose_weight', 'lightly_active', ?
                )
                """,
                (f"prof_{uuid.uuid4().hex[:12]}", user_id, email, full_name, now),
            )
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
            prof = cur.fetchone()

    token = create_access_token(user_id=user_id, email=email, full_name=full_name)
    _set_auth_cookie(response, token)

    return UserProfileResponse(
        id=user_id,
        email=email,
        full_name=prof["full_name"] or full_name,
        age=prof["age"],
        gender=prof["gender"],
        height_cm=float(prof["height_cm"]),
        weight_kg=float(prof["weight_kg"]),
        goal=prof["goal"],
        activity_level=prof["activity_level"],
        daily_calorie_target=int(prof["target_calories"]),
        is_solo_cook=bool(prof["is_solo_cook"]),
        active_meal_frequency=prof["active_meal_frequency"],
        token=token,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clears the session cookie and terminates user session."""
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )
    return {"status": "success", "message": "Successfully logged out"}


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(user_payload: dict = Depends(get_current_user)):
    """
    Returns the profile of the verified authenticated user.
    Loads data directly from local SQLite.
    """
    user_id = user_payload["id"]
    email = normalize_email(user_payload.get("email") or "")

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        prof = cur.fetchone()

        if not prof:
            now = datetime.now(timezone.utc).isoformat()
            meta = user_payload.get("user_metadata", {})
            full_name = meta.get("full_name") or (email.split("@")[0] if email else "User")
            cur.execute(
                """
                INSERT OR IGNORE INTO profiles (
                    id, user_id, email, full_name, dietary_pref, allergies,
                    target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                    active_meal_frequency, age, gender, height_cm, weight_kg,
                    goal, activity_level, updated_at
                ) VALUES (
                    ?, ?, ?, ?, 'vegetarian', '[]',
                    1850, 100.0, 30, 1,
                    '3_meals', 26, 'male', 175.0, 75.0,
                    'lose_weight', 'lightly_active', ?
                )
                """,
                (f"prof_{uuid.uuid4().hex[:12]}", user_id, email, full_name, now),
            )
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
            prof = cur.fetchone()

    return UserProfileResponse(
        id=user_id,
        email=prof["email"] if prof else email,
        full_name=prof["full_name"] if prof else "User",
        age=prof["age"] if prof else 26,
        gender=prof["gender"] if prof else "male",
        height_cm=float(prof["height_cm"]) if prof else 175.0,
        weight_kg=float(prof["weight_kg"]) if prof else 75.0,
        goal=prof["goal"] if prof else "lose_weight",
        activity_level=prof["activity_level"] if prof else "lightly_active",
        daily_calorie_target=int(prof["target_calories"]) if prof else 1850,
        is_solo_cook=bool(prof["is_solo_cook"]) if prof else True,
        active_meal_frequency=prof["active_meal_frequency"] if prof else "3_meals",
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    req: UserUpdateRequest,
    user_payload: dict = Depends(get_current_user),
):
    """
    Updates user biometrics and profile in local SQLite,
    recalculating target calories accordingly.
    """
    user_id = user_payload["id"]
    email = normalize_email(user_payload.get("email") or "")
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        prof = cur.fetchone()
        if not prof:
            # Insert baseline
            cur.execute(
                """
                INSERT INTO profiles (
                    id, user_id, email, full_name, dietary_pref, allergies,
                    target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                    active_meal_frequency, age, gender, height_cm, weight_kg,
                    goal, activity_level, updated_at
                ) VALUES (
                    ?, ?, ?, ?, 'vegetarian', '[]',
                    1850, 100.0, 30, 1,
                    '3_meals', 26, 'male', 175.0, 75.0,
                    'lose_weight', 'lightly_active', ?
                )
                """,
                (f"prof_{uuid.uuid4().hex[:12]}", user_id, email, email.split("@")[0], now),
            )
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
            prof = cur.fetchone()

        current_data = dict(prof)
        for key, val in req.model_dump(exclude_unset=True).items():
            if val is not None:
                current_data[key] = val.value if hasattr(val, "value") else val

        target_cal = _calculate_target_calories(
            weight_kg=float(current_data["weight_kg"]),
            height_cm=float(current_data["height_cm"]),
            age=int(current_data["age"]),
            gender=str(current_data["gender"]),
            activity_level=str(current_data["activity_level"]),
            goal=str(current_data["goal"]),
        )
        current_data["target_calories"] = target_cal

        cur.execute(
            """
            UPDATE profiles SET
                full_name = ?,
                age = ?,
                gender = ?,
                height_cm = ?,
                weight_kg = ?,
                goal = ?,
                activity_level = ?,
                target_calories = ?,
                is_solo_cook = ?,
                active_meal_frequency = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                current_data["full_name"],
                current_data["age"],
                current_data["gender"],
                current_data["height_cm"],
                current_data["weight_kg"],
                current_data["goal"],
                current_data["activity_level"],
                target_cal,
                1 if current_data["is_solo_cook"] else 0,
                current_data["active_meal_frequency"],
                now,
                user_id,
            ),
        )

        if req.full_name is not None:
            cur.execute("UPDATE users SET full_name = ?, updated_at = ? WHERE id = ?", (req.full_name, now, user_id))

    return UserProfileResponse(
        id=user_id,
        email=current_data["email"],
        full_name=current_data["full_name"],
        age=current_data["age"],
        gender=current_data["gender"],
        height_cm=float(current_data["height_cm"]),
        weight_kg=float(current_data["weight_kg"]),
        goal=current_data["goal"],
        activity_level=current_data["activity_level"],
        daily_calorie_target=target_cal,
        is_solo_cook=bool(current_data["is_solo_cook"]),
        active_meal_frequency=current_data["active_meal_frequency"],
    )
