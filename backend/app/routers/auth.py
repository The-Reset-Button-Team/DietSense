"""
DietSense — Authentication & Profile Routes
Hybrid local-first authentication architecture:
- Local database-backed authentication using bcrypt password hashing, session cookies, and JWT.
- Supabase Auth integration (email registration, login, token verification, password reset).
- Secure account linking with stable internal DietSense user IDs.
- Duplicate account prevention and strict user data isolation.
- Offline and local fallback handling.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    UserUpdateRequest,
    SupabaseLoginRequest,
    SupabaseTokenVerifyRequest,
    AccountLinkRequest,
    PasswordResetRequest,
)
from app.core.config import settings
from app.core.security import (
    normalize_email,
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.dependencies import get_current_user
from app.core.auth_service import (
    verify_supabase_token,
    resolve_supabase_identity,
    link_supabase_account,
    get_user_auth_providers,
    supabase_register_user,
    supabase_login_user,
    supabase_request_password_reset,
    get_supabase_anon_client,
)
from db.database import get_db_cursor, get_connection
from app.core.sync_service import enqueue_sync_operation

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


def _build_profile_response(user_id: str, email: str, prof: dict, token: str = None) -> UserProfileResponse:
    """Constructs a unified UserProfileResponse including active auth providers."""
    providers = get_user_auth_providers(user_id)
    return UserProfileResponse(
        id=user_id,
        email=prof.get("email") or email,
        full_name=prof.get("full_name") or (email.split("@")[0] if email else "User"),
        age=prof.get("age", 26),
        gender=prof.get("gender", "male"),
        height_cm=float(prof.get("height_cm", 175.0)),
        weight_kg=float(prof.get("weight_kg", 75.0)),
        goal=prof.get("goal", "lose_weight"),
        activity_level=prof.get("activity_level", "lightly_active"),
        daily_calorie_target=int(prof.get("target_calories", 1850)),
        is_solo_cook=bool(prof.get("is_solo_cook", 1)),
        active_meal_frequency=prof.get("active_meal_frequency", "3_meals"),
        token=token,
        auth_providers=providers,
    )


# ─── LOCAL AUTHENTICATION (Preserved & Offline-Ready) ─────────────────────────

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
        # Check if email is already registered locally
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

        # Insert auth identity for local provider
        ident_id = f"ident_{uuid.uuid4().hex[:12]}"
        cur.execute(
            """
            INSERT OR IGNORE INTO auth_identities (id, user_id, provider, provider_user_id, email, created_at, updated_at)
            VALUES (?, ?, 'local', ?, ?, ?, ?)
            """,
            (ident_id, user_id, user_id, email, now, now),
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
        auth_providers=["local"],
    )


@router.post("/login", response_model=UserProfileResponse)
async def login(req: UserLoginRequest, response: Response):
    """
    Authenticates a user using email and password against local SQLite.
    Verifies bcrypt hash, sets HttpOnly cookie, and returns user profile + token.
    Works completely offline without external network dependencies.
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

    return _build_profile_response(user_id=user_id, email=email, prof=dict(prof), token=token)


# ─── SUPABASE AUTHENTICATION ─────────────────────────────────────────────────

@router.post("/supabase/register", response_model=UserProfileResponse)
async def supabase_register(req: UserRegisterRequest, response: Response):
    """
    Registers a new user through Supabase Auth.
    Checks for duplicate accounts, provisions a stable internal DietSense user ID,
    maps the Supabase UUID in auth_identities, sets session cookie, and returns profile.
    """
    target_cal = _calculate_target_calories(
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        age=req.age,
        gender=req.gender.value,
        activity_level=req.activity_level.value,
        goal=req.goal.value,
    )

    biometrics = {
        "age": req.age,
        "gender": req.gender.value,
        "height_cm": req.height_cm,
        "weight_kg": req.weight_kg,
        "goal": req.goal.value,
        "activity_level": req.activity_level.value,
        "target_calories": target_cal,
    }

    internal_user_id, token, extra = supabase_register_user(
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        biometrics=biometrics,
    )

    _set_auth_cookie(response, token)

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (internal_user_id,))
        prof = cur.fetchone()

    return _build_profile_response(
        user_id=internal_user_id,
        email=normalize_email(req.email),
        prof=dict(prof) if prof else {},
        token=token,
    )


@router.post("/supabase/login", response_model=UserProfileResponse)
async def supabase_login(req: SupabaseLoginRequest, response: Response):
    """
    Authenticates a user against Supabase Auth.
    Resolves the stable internal DietSense user ID from Supabase UUID,
    sets the session cookie, and returns the profile.
    """
    internal_user_id, token, extra = supabase_login_user(
        email=req.email,
        password=req.password,
    )

    _set_auth_cookie(response, token)

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (internal_user_id,))
        prof = cur.fetchone()

    return _build_profile_response(
        user_id=internal_user_id,
        email=normalize_email(req.email),
        prof=dict(prof) if prof else {},
        token=token,
    )


@router.post("/supabase/verify", response_model=UserProfileResponse)
async def supabase_verify_token(req: SupabaseTokenVerifyRequest, response: Response):
    """
    Exchanges a verified Supabase access token (e.g. from client SDK or OAuth)
    for a stable internal DietSense session and cookie.
    Validates token via Supabase GoTrue Auth service (never misusing API keys as secrets).
    """
    sb_user = verify_supabase_token(req.access_token)
    supabase_uid = sb_user["id"]
    email = sb_user.get("email") or ""
    full_name = sb_user.get("user_metadata", {}).get("full_name") or email.split("@")[0]

    internal_user_id = resolve_supabase_identity(
        supabase_user_id=supabase_uid,
        email=email,
        full_name=full_name,
        metadata=sb_user.get("user_metadata", {}),
        auto_link_verified=True,
    )

    token = create_access_token(
        user_id=internal_user_id,
        email=email,
        full_name=full_name,
    )
    _set_auth_cookie(response, token)

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (internal_user_id,))
        prof = cur.fetchone()

    return _build_profile_response(
        user_id=internal_user_id,
        email=email,
        prof=dict(prof) if prof else {},
        token=token,
    )


# ─── ACCOUNT LINKING ─────────────────────────────────────────────────────────

@router.post("/link/supabase")
async def link_supabase(
    req: AccountLinkRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Securely links a Supabase identity to the currently authenticated DietSense account.
    Validates that the Supabase account is not already linked to another user.
    """
    internal_user_id = current_user["id"]
    supabase_uid = None
    email = None

    if req.access_token:
        sb_user = verify_supabase_token(req.access_token)
        supabase_uid = sb_user["id"]
        email = sb_user.get("email") or ""
    elif req.email and req.password:
        client = get_supabase_anon_client()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth service is not available",
            )
        try:
            res = client.auth.sign_in_with_password({
                "email": normalize_email(str(req.email)),
                "password": req.password,
            })
            if not res.user:
                raise HTTPException(status_code=401, detail="Invalid Supabase credentials")
            supabase_uid = str(res.user.id)
            email = str(res.user.email)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Supabase authentication failed: {e}")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either access_token or email + password to link Supabase account",
        )

    link_supabase_account(
        internal_user_id=internal_user_id,
        supabase_user_id=supabase_uid,
        email=email,
    )

    providers = get_user_auth_providers(internal_user_id)
    return {
        "status": "success",
        "message": "Supabase account linked successfully",
        "user_id": internal_user_id,
        "auth_providers": providers,
    }


@router.delete("/link/supabase")
async def unlink_supabase(current_user: dict = Depends(get_current_user)):
    """
    Unlinks the Supabase identity from the authenticated account.
    Fails safely if Supabase is the user's only authentication method.
    """
    user_id = current_user["id"]
    providers = get_user_auth_providers(user_id)

    if "local" not in providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink Supabase because you do not have a local password set.",
        )

    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM auth_identities WHERE user_id = ? AND provider = 'supabase'",
            (user_id,),
        )

    return {
        "status": "success",
        "message": "Supabase account unlinked successfully",
        "auth_providers": get_user_auth_providers(user_id),
    }


# ─── PASSWORD RESET ──────────────────────────────────────────────────────────

@router.post("/reset-password")
async def reset_password(req: PasswordResetRequest):
    """
    Initiates a password reset for a user.
    If the user has a linked Supabase identity, triggers Supabase's GoTrue email reset.
    Returns success message to prevent user enumeration.
    """
    email = normalize_email(req.email)
    supabase_request_password_reset(email)
    return {
        "status": "success",
        "message": "If an account with that email exists, password reset instructions have been sent.",
    }


# ─── LOGOUT & SESSION MANAGEMENT ─────────────────────────────────────────────

@router.post("/logout")
async def logout(response: Response):
    """
    Clears the HttpOnly session cookie and terminates the user session.
    Signs out from Supabase client if configured.
    """
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )
    client = get_supabase_anon_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    return {"status": "success", "message": "Successfully logged out"}


# ─── PROFILE RETRIEVAL & UPDATE ──────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(user_payload: dict = Depends(get_current_user)):
    """
    Returns the profile of the verified authenticated user.
    Loads data directly from local SQLite and includes linked auth providers.
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

    return _build_profile_response(
        user_id=user_id,
        email=email,
        prof=dict(prof) if prof else {},
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

    enqueue_sync_operation(
        user_id=user_id,
        entity_type="profile",
        entity_id=user_id,
        operation="UPSERT",
        payload=current_data,
    )

    return _build_profile_response(
        user_id=user_id,
        email=current_data["email"],
        prof=current_data,
    )
