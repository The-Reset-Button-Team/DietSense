"""
DietSense — Authentication Service & Provider Integration
Handles:
- Supabase Auth API calls (signUp, signIn, resetPassword, getUser)
- Strict Supabase JWT / token validation without treating API keys as signing secrets
- Identity mapping between Supabase UUIDs and internal DietSense user IDs (`usr_<hex>`)
- Secure account linking and unlinking
- Duplicate account prevention
- Offline and local fallback handling
"""

import uuid
import time
import jwt
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security import normalize_email, create_access_token
from db.database import get_db_cursor

try:
    from supabase import create_client, Client
    from supabase_auth.errors import AuthApiError
except ImportError:
    create_client = None
    Client = None
    AuthApiError = Exception


# ─── Supabase Client Initializers ─────────────────────────────────────────────

def get_supabase_anon_client():
    """
    Returns a client initialized with the public anon key.
    Safe for user sign-in and sign-up requests.
    """
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_anon_key", "") or getattr(settings, "supabase_publishable_key", "")
    if not url or not key or key.startswith("[YOUR"):
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"[auth_service] Failed to create anon Supabase client: {e}")
        return None


def get_supabase_admin_client():
    """
    Returns a client initialized with the service role key.
    Used exclusively for backend-level administrative verification.
    """
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "") or getattr(settings, "supabase_secret_key", "")
    if not url or not key or key.startswith("[YOUR"):
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"[auth_service] Failed to create admin Supabase client: {e}")
        return None


# ─── Token Verification (Never Treat API Keys as JWT Secrets) ────────────────

def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Validates a Supabase authentication token.
    
    Security enforcement:
    1. NEVER treats API keys (anon key, service role key) as JWT signing secrets.
    2. Validates token directly with Supabase Auth service (GoTrue) via get_user(token).
    3. If configured and valid, supports verifying against SUPABASE_JWT_SECRET.
    4. Enforces expiration and claims.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token: token is missing or malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. First attempt: Verify via Supabase Auth GoTrue service
    admin_client = get_supabase_admin_client() or get_supabase_anon_client()
    if admin_client:
        try:
            response = admin_client.auth.get_user(token)
            if response and response.user:
                u = response.user
                return {
                    "id": str(u.id),
                    "email": normalize_email(getattr(u, "email", "") or ""),
                    "user_metadata": getattr(u, "user_metadata", {}) or {},
                    "app_metadata": getattr(u, "app_metadata", {}) or {},
                    "email_confirmed_at": getattr(u, "email_confirmed_at", None),
                }
        except AuthApiError as e:
            msg = str(e).lower()
            if "expired" in msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Supabase authentication token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            # Network issue or service unavailable
            err_str = str(e).lower()
            if "connection" in err_str or "timeout" in err_str or "failed to establish" in err_str:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Supabase Auth service is currently unreachable",
                )

    # 2. Second attempt: Direct cryptographic check if SUPABASE_JWT_SECRET is explicitly configured
    supabase_jwt_secret = getattr(settings, "supabase_jwt_secret", "")
    if supabase_jwt_secret and not supabase_jwt_secret.startswith("[YOUR"):
        try:
            payload = jwt.decode(
                token,
                supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True, "verify_aud": True},
            )
            return {
                "id": str(payload.get("sub", "")),
                "email": normalize_email(payload.get("email", "")),
                "user_metadata": payload.get("user_metadata", {}),
                "app_metadata": payload.get("app_metadata", {}),
                "email_confirmed_at": payload.get("email_confirmed_at"),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Supabase credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ─── Identity Resolution & Account Mapping ───────────────────────────────────

def get_user_auth_providers(user_id: str) -> List[str]:
    """Returns the list of active authentication providers for an internal user ID."""
    providers = []
    with get_db_cursor() as cur:
        # Check password hash in users table
        cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row and row["password_hash"] and not row["password_hash"].startswith("!"):
            providers.append("local")

        # Check auth_identities table
        cur.execute("SELECT provider FROM auth_identities WHERE user_id = ?", (user_id,))
        for identity in cur.fetchall():
            prov = identity["provider"]
            if prov not in providers:
                providers.append(prov)

    return providers or ["local"]


def resolve_supabase_identity(
    supabase_user_id: str,
    email: str,
    full_name: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    auto_link_verified: bool = True,
) -> str:
    """
    Maps a Supabase user ID (UUID) to a stable internal DietSense user ID (`usr_<hex>`).
    
    1. If mapping exists in `auth_identities`, returns existing `user_id`.
    2. If no mapping exists:
       - If email exists in `users`:
         - If auto_link_verified is True: securely links Supabase identity to existing internal user.
         - Else: raises conflict 409 to prevent unauthorized linking.
       - If email does not exist in `users`:
         - Provisions new internal user ID (`usr_<hex>`).
         - Creates `users` record (`password_hash = '!supabase_managed'`).
         - Creates default `profiles` record.
         - Records mapping in `auth_identities`.
    
    Maintains foreign key integrity across all DietSense SQLite tables.
    """
    normalized = normalize_email(email)
    now = datetime.now(timezone.utc).isoformat()
    meta = metadata or {}
    display_name = full_name or meta.get("full_name") or (normalized.split("@")[0] if normalized else "User")

    with get_db_cursor() as cur:
        # 1. Check existing mapping
        cur.execute(
            "SELECT user_id FROM auth_identities WHERE provider = 'supabase' AND provider_user_id = ?",
            (supabase_user_id,),
        )
        row = cur.fetchone()
        if row:
            return row["user_id"]

        # 2. Check if a local user with this email already exists
        cur.execute("SELECT id, full_name FROM users WHERE email = ? COLLATE NOCASE", (normalized,))
        existing_user = cur.fetchone()

        if existing_user:
            internal_user_id = existing_user["id"]
            if not auto_link_verified:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists locally. Please sign in locally to link your account.",
                )

            # Check if this user already linked a DIFFERENT supabase user ID
            cur.execute(
                "SELECT provider_user_id FROM auth_identities WHERE user_id = ? AND provider = 'supabase'",
                (internal_user_id,),
            )
            linked_sb = cur.fetchone()
            if linked_sb and linked_sb["provider_user_id"] != supabase_user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This internal account is already linked to a different Supabase account.",
                )

            # Link the Supabase identity to the existing user
            ident_id = f"ident_{uuid.uuid4().hex[:12]}"
            cur.execute(
                """
                INSERT OR IGNORE INTO auth_identities (id, user_id, provider, provider_user_id, email, created_at, updated_at)
                VALUES (?, ?, 'supabase', ?, ?, ?, ?)
                """,
                (ident_id, internal_user_id, supabase_user_id, normalized, now, now),
            )
            return internal_user_id

        # 3. New user provisioning
        internal_user_id = f"usr_{uuid.uuid4().hex[:12]}"
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, '!supabase_managed', ?, 'active', ?, ?)
            """,
            (internal_user_id, normalized, display_name, now, now),
        )

        # Create default profile
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
                1850, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', '["indian"]', ?
            )
            """,
            (prof_id, internal_user_id, normalized, display_name, now),
        )

        # Register mapping
        ident_id = f"ident_{uuid.uuid4().hex[:12]}"
        cur.execute(
            """
            INSERT INTO auth_identities (id, user_id, provider, provider_user_id, email, created_at, updated_at)
            VALUES (?, ?, 'supabase', ?, ?, ?, ?)
            """,
            (ident_id, internal_user_id, supabase_user_id, normalized, now, now),
        )

        return internal_user_id


def link_supabase_account(internal_user_id: str, supabase_user_id: str, email: str) -> None:
    """
    Securely links a verified Supabase identity to an authenticated internal DietSense user.
    Prevents duplicate linkings and cross-account takeovers.
    """
    normalized = normalize_email(email)
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        # Verify internal user exists
        cur.execute("SELECT id FROM users WHERE id = ?", (internal_user_id,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Internal user not found",
            )

        # Verify Supabase account is not linked to someone else
        cur.execute(
            "SELECT user_id FROM auth_identities WHERE provider = 'supabase' AND provider_user_id = ?",
            (supabase_user_id,),
        )
        existing = cur.fetchone()
        if existing:
            if existing["user_id"] == internal_user_id:
                return  # Already linked to this user
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Supabase account is already linked to another DietSense user.",
            )

        # Verify internal user does not already have a different Supabase account linked
        cur.execute(
            "SELECT provider_user_id FROM auth_identities WHERE user_id = ? AND provider = 'supabase'",
            (internal_user_id,),
        )
        current_sb = cur.fetchone()
        if current_sb:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Your account is already linked to a different Supabase identity.",
            )

        # Link identity
        ident_id = f"ident_{uuid.uuid4().hex[:12]}"
        cur.execute(
            """
            INSERT INTO auth_identities (id, user_id, provider, provider_user_id, email, created_at, updated_at)
            VALUES (?, ?, 'supabase', ?, ?, ?, ?)
            """,
            (ident_id, internal_user_id, supabase_user_id, normalized, now, now),
        )


# ─── Supabase Authentication Operations ───────────────────────────────────────

def supabase_register_user(
    email: str,
    password: str,
    full_name: str,
    biometrics: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Registers a new user through Supabase Auth.
    Checks for duplicate accounts, provisions internal user ID, and returns
    (internal_user_id, dietsense_token, profile_data).
    """
    normalized = normalize_email(email)

    # 1. Duplicate check in local SQLite
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (normalized,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    client = get_supabase_anon_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth service is not configured or unavailable",
        )

    try:
        auth_res = client.auth.sign_up({
            "email": normalized,
            "password": password,
            "options": {
                "data": {"full_name": full_name},
            },
        })
    except AuthApiError as e:
        err_msg = str(e).lower()
        if "already registered" in err_msg or "already exists" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists in Supabase",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supabase registration error: {e}",
        )
    except Exception as e:
        err_str = str(e).lower()
        if "connection" in err_str or "timeout" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth service is currently unreachable",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {e}",
        )

    if not auth_res.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user in Supabase",
        )

    supabase_user_id = str(auth_res.user.id)
    internal_user_id = resolve_supabase_identity(
        supabase_user_id=supabase_user_id,
        email=normalized,
        full_name=full_name,
        metadata={"full_name": full_name},
    )

    # Update profile with biometrics if provided
    if biometrics:
        with get_db_cursor() as cur:
            cur.execute(
                """
                UPDATE profiles SET
                    age = COALESCE(?, age),
                    gender = COALESCE(?, gender),
                    height_cm = COALESCE(?, height_cm),
                    weight_kg = COALESCE(?, weight_kg),
                    goal = COALESCE(?, goal),
                    activity_level = COALESCE(?, activity_level),
                    target_calories = COALESCE(?, target_calories)
                WHERE user_id = ?
                """,
                (
                    biometrics.get("age"),
                    biometrics.get("gender"),
                    biometrics.get("height_cm"),
                    biometrics.get("weight_kg"),
                    biometrics.get("goal"),
                    biometrics.get("activity_level"),
                    biometrics.get("target_calories"),
                    internal_user_id,
                ),
            )

    token = create_access_token(
        user_id=internal_user_id,
        email=normalized,
        full_name=full_name,
    )

    return internal_user_id, token, {"supabase_user_id": supabase_user_id}


def supabase_login_user(email: str, password: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Authenticates a user against Supabase Auth.
    Resolves the internal user ID, creates a DietSense session token, and returns
    (internal_user_id, dietsense_token, profile_data).
    """
    normalized = normalize_email(email)
    client = get_supabase_anon_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth service is not configured or unavailable",
        )

    try:
        auth_res = client.auth.sign_in_with_password({
            "email": normalized,
            "password": password,
        })
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except Exception as e:
        err_str = str(e).lower()
        if "connection" in err_str or "timeout" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth service is currently unreachable",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with Supabase Auth",
        )

    if not auth_res.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    supabase_user_id = str(auth_res.user.id)
    full_name = getattr(auth_res.user, "user_metadata", {}).get("full_name", "") or normalized.split("@")[0]

    internal_user_id = resolve_supabase_identity(
        supabase_user_id=supabase_user_id,
        email=normalized,
        full_name=full_name,
        metadata=getattr(auth_res.user, "user_metadata", {}),
        auto_link_verified=True,
    )

    token = create_access_token(
        user_id=internal_user_id,
        email=normalized,
        full_name=full_name,
    )

    return internal_user_id, token, {"supabase_user_id": supabase_user_id}


def supabase_request_password_reset(email: str) -> bool:
    """Sends a password reset email via Supabase GoTrue Auth."""
    normalized = normalize_email(email)
    client = get_supabase_anon_client()
    if not client:
        return False
    try:
        client.auth.reset_password_for_email(normalized)
        return True
    except Exception as e:
        print(f"[auth_service] Password reset request notice: {e}")
        return False
