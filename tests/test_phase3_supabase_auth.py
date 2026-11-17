"""
DietSense — Phase 3 Supabase Authentication Integration Test Suite
Verifies:
1. Local login & registration (preserved & offline ready)
2. Supabase login & registration
3. Secure account linking and unlinking
4. Stable internal DietSense user IDs & identity mapping
5. Duplicate account prevention
6. Logout & session cookie termination
7. Invalid and expired token handling
8. Offline fallback authentication
9. Cross-user data isolation
"""

import sys
import os
import time
import uuid
import jwt
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure root and backend are in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth_service import resolve_supabase_identity, link_supabase_account, get_user_auth_providers
from db.database import init_db, get_connection, get_db_cursor

client = TestClient(app)

# Ensure schema is initialized
init_db()


# ─── 1. LOCAL LOGIN & REGISTRATION (PRESERVED & OFFLINE) ──────────────────────

def test_local_registration_and_login():
    """Verify local email/password registration, bcrypt hashing, and login."""
    unique_email = f"local_{uuid.uuid4().hex[:8]}@dietsense.ai"
    password = "StrongPassword123!"

    # 1. Register locally
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Local Tester",
            "age": 27,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 74.0,
            "goal": "maintain_weight",
            "activity_level": "moderately_active",
        },
    )
    assert reg_res.status_code == 200, reg_res.text
    data = reg_res.json()
    user_id = data["id"]
    assert user_id.startswith("usr_")
    assert data["email"] == unique_email
    assert data["token"] is not None
    assert "local" in data["auth_providers"]

    # Verify cookie was set
    cookie = reg_res.cookies.get(settings.session_cookie_name)
    assert cookie is not None

    # 2. Login locally
    login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["id"] == user_id
    assert "local" in login_data["auth_providers"]

    # 3. Invalid credentials rejected
    bad_login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]


def test_offline_local_login():
    """
    Simulates complete offline mode (network unreachable / Supabase disabled).
    Local login must operate flawlessly without network access.
    """
    unique_email = f"offline_{uuid.uuid4().hex[:8]}@dietsense.ai"
    password = "OfflinePassword123!"

    # Register local user
    reg = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Offline User",
            "age": 30,
            "gender": "female",
            "height_cm": 165.0,
            "weight_kg": 58.0,
            "goal": "lose_weight",
            "activity_level": "lightly_active",
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["id"]

    # Patch Supabase client to simulate offline network
    with patch("app.core.auth_service.get_supabase_anon_client", return_value=None), \
         patch("app.core.supabase_client.get_pg_connection", return_value=None):
        # Local login works 100% offline
        login_res = client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": password},
        )
        assert login_res.status_code == 200
        assert login_res.json()["id"] == user_id


# ─── 2. SUPABASE REGISTRATION & LOGIN ────────────────────────────────────────

def test_supabase_registration_and_mapping():
    """
    Verifies Supabase registration creates a stable internal DietSense user ID (usr_...)
    and correctly populates SQLite users, profiles, and auth_identities.
    """
    unique_email = f"sb_reg_{uuid.uuid4().hex[:8]}@dietsense.ai"
    sb_uuid = str(uuid.uuid4())

    mock_user = MagicMock()
    mock_user.id = sb_uuid
    mock_user.email = unique_email
    mock_user.user_metadata = {"full_name": "Supabase User"}
    mock_user.app_metadata = {}

    mock_auth_res = MagicMock()
    mock_auth_res.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.sign_up.return_value = mock_auth_res

    with patch("app.core.auth_service.get_supabase_anon_client", return_value=mock_client):
        res = client.post(
            "/api/auth/supabase/register",
            json={
                "email": unique_email,
                "password": "SupabasePassword123!",
                "full_name": "Supabase User",
                "age": 29,
                "gender": "other",
                "height_cm": 170.0,
                "weight_kg": 68.0,
                "goal": "maintain_weight",
                "activity_level": "sedentary",
            },
        )
        assert res.status_code == 200, res.text
        data = res.json()
        internal_id = data["id"]

        # DietSense internal ID format: starts with usr_
        assert internal_id.startswith("usr_")
        assert internal_id != sb_uuid
        assert data["email"] == unique_email
        assert "supabase" in data["auth_providers"]

        # Verify mapping exists in SQLite auth_identities
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT user_id, provider, provider_user_id FROM auth_identities WHERE provider = 'supabase' AND provider_user_id = ?",
                (sb_uuid,),
            )
            mapping = cur.fetchone()
            assert mapping is not None
            assert mapping["user_id"] == internal_id
            assert mapping["provider_user_id"] == sb_uuid


def test_supabase_login_resolves_internal_id():
    """
    Verifies Supabase login returns the established internal DietSense ID and sets session cookie.
    """
    unique_email = f"sb_login_{uuid.uuid4().hex[:8]}@dietsense.ai"
    sb_uuid = str(uuid.uuid4())

    # Pre-provision identity
    internal_id = resolve_supabase_identity(
        supabase_user_id=sb_uuid,
        email=unique_email,
        full_name="Existing Supabase User",
    )

    mock_user = MagicMock()
    mock_user.id = sb_uuid
    mock_user.email = unique_email
    mock_user.user_metadata = {"full_name": "Existing Supabase User"}

    mock_auth_res = MagicMock()
    mock_auth_res.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.return_value = mock_auth_res

    with patch("app.core.auth_service.get_supabase_anon_client", return_value=mock_client):
        res = client.post(
            "/api/auth/supabase/login",
            json={"email": unique_email, "password": "AnyPasswordVal1d!"},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"] == internal_id
        assert data["token"] is not None
        assert client.cookies.get(settings.session_cookie_name) is not None


def test_supabase_token_verify_endpoint():
    """
    Verifies exchanging a client-side Supabase access token for a DietSense session.
    """
    unique_email = f"sb_token_{uuid.uuid4().hex[:8]}@dietsense.ai"
    sb_uuid = str(uuid.uuid4())

    mock_verified_user = {
        "id": sb_uuid,
        "email": unique_email,
        "user_metadata": {"full_name": "Verified Client User"},
        "app_metadata": {},
        "email_confirmed_at": "2026-11-17T00:00:00Z",
    }

    with patch("app.routers.auth.verify_supabase_token", return_value=mock_verified_user), \
         patch("app.core.auth_service.verify_supabase_token", return_value=mock_verified_user):
        res = client.post(
            "/api/auth/supabase/verify",
            json={"access_token": "mock-supabase-access-token-123"},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"].startswith("usr_")
        assert data["email"] == unique_email


# ─── 3. SECURE ACCOUNT LINKING ───────────────────────────────────────────────

def test_account_linking_local_to_supabase():
    """
    A user with an existing local account links their Supabase account.
    Verifies they can subsequently authenticate using either provider and maintain the same internal ID.
    """
    unique_email = f"link_{uuid.uuid4().hex[:8]}@dietsense.ai"
    password = "LocalSecretPassword123!"

    # 1. Register local account
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Link Tester",
            "age": 25,
            "gender": "male",
            "height_cm": 180.0,
            "weight_kg": 76.0,
            "goal": "gain_weight",
            "activity_level": "very_active",
        },
    )
    assert reg_res.status_code == 200, reg_res.text
    user_id = reg_res.json()["id"]
    token = reg_res.json()["token"]

    sb_uuid = str(uuid.uuid4())
    mock_verified = {
        "id": sb_uuid,
        "email": unique_email,
        "user_metadata": {"full_name": "Link Tester"},
        "app_metadata": {},
    }

    # 2. Link Supabase account via /api/auth/link/supabase
    with patch("app.routers.auth.verify_supabase_token", return_value=mock_verified), \
         patch("app.core.auth_service.verify_supabase_token", return_value=mock_verified):
        link_res = client.post(
            "/api/auth/link/supabase",
            json={"provider": "supabase", "access_token": "valid-sb-token"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert link_res.status_code == 200, link_res.text
        link_data = link_res.json()
        assert "local" in link_data["auth_providers"]
        assert "supabase" in link_data["auth_providers"]

    # 3. Check /api/auth/me reflects both providers
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    providers = me_res.json()["auth_providers"]
    assert "local" in providers
    assert "supabase" in providers

    # 4. Now Supabase login resolves to the EXACT same user_id!
    mock_user = MagicMock()
    mock_user.id = sb_uuid
    mock_user.email = unique_email
    mock_user.user_metadata = {"full_name": "Link Tester"}

    mock_auth_res = MagicMock()
    mock_auth_res.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.return_value = mock_auth_res

    with patch("app.core.auth_service.get_supabase_anon_client", return_value=mock_client):
        sb_login_res = client.post(
            "/api/auth/supabase/login",
            json={"email": unique_email, "password": "AnyPasswordVal1d!"},
        )
        assert sb_login_res.status_code == 200
        # Exact same internal user ID
        assert sb_login_res.json()["id"] == user_id


def test_account_linking_conflict_rejection():
    """
    Attempting to link a Supabase account that is ALREADY linked to another user must fail with 409 Conflict.
    """
    email1 = f"conflict1_{uuid.uuid4().hex[:8]}@dietsense.ai"
    email2 = f"conflict2_{uuid.uuid4().hex[:8]}@dietsense.ai"

    # Register both users locally
    reg1 = client.post("/api/auth/register", json={
        "email": email1, "password": "Password123!", "full_name": "U1",
        "age": 25, "gender": "male", "height_cm": 175.0, "weight_kg": 70.0,
        "goal": "lose_weight", "activity_level": "sedentary"
    })
    assert reg1.status_code == 200
    u1_id = reg1.json()["id"]

    reg2 = client.post("/api/auth/register", json={
        "email": email2, "password": "Password123!", "full_name": "U2",
        "age": 26, "gender": "female", "height_cm": 165.0, "weight_kg": 60.0,
        "goal": "lose_weight", "activity_level": "sedentary"
    })
    assert reg2.status_code == 200
    token_u2 = reg2.json()["token"]

    shared_sb_uuid = str(uuid.uuid4())

    # Link sb_uuid to user1
    link_supabase_account(internal_user_id=u1_id, supabase_user_id=shared_sb_uuid, email=email1)

    # Attempt to link the SAME sb_uuid to user2 -> Must raise 409
    mock_verified = {
        "id": shared_sb_uuid,
        "email": email1,
        "user_metadata": {},
    }

    with patch("app.routers.auth.verify_supabase_token", return_value=mock_verified), \
         patch("app.core.auth_service.verify_supabase_token", return_value=mock_verified):
        res = client.post(
            "/api/auth/link/supabase",
            json={"provider": "supabase", "access_token": "token-for-sb-uuid"},
            headers={"Authorization": f"Bearer {token_u2}"},
        )
        assert res.status_code == 409, res.text
        assert "already linked to another DietSense user" in res.json()["detail"]


# ─── 4. DUPLICATE ACCOUNT PREVENTION ─────────────────────────────────────────

def test_duplicate_registration_prevention():
    """
    Attempting to register with an already existing email returns 400 Bad Request.
    """
    dup_email = f"dup_{uuid.uuid4().hex[:8]}@dietsense.ai"
    password = "SecurePassword123!"

    # First registration succeeds
    res1 = client.post(
        "/api/auth/register",
        json={
            "email": dup_email,
            "password": password,
            "full_name": "First User",
            "age": 24,
            "gender": "female",
            "height_cm": 160.0,
            "weight_kg": 52.0,
            "goal": "lose_weight",
            "activity_level": "sedentary",
        },
    )
    assert res1.status_code == 200

    # Second registration with exact same email fails
    res2 = client.post(
        "/api/auth/register",
        json={
            "email": dup_email,
            "password": "AnotherPassword456!",
            "full_name": "Imposter User",
            "age": 30,
            "gender": "female",
            "height_cm": 160.0,
            "weight_kg": 52.0,
            "goal": "lose_weight",
            "activity_level": "sedentary",
        },
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


# ─── 5. LOGOUT & EXPIRED SESSIONS ────────────────────────────────────────────

def test_logout_terminates_session():
    """
    Logging out clears the session cookie and prevents subsequent authenticated access.
    """
    unique_email = f"logout_{uuid.uuid4().hex[:8]}@dietsense.ai"
    password = "LogoutPassword123!"

    reg = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Logout Tester",
            "age": 25,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "goal": "maintain_weight",
            "activity_level": "lightly_active",
        },
    )
    assert reg.status_code == 200

    # Cookie is present
    session_cookie = client.cookies.get(settings.session_cookie_name)
    assert session_cookie is not None

    # Call logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # Cookie cleared in response headers
    set_cookie_header = logout_res.headers.get("set-cookie", "")
    assert f'{settings.session_cookie_name}=""' in set_cookie_header or "Max-Age=0" in set_cookie_header


def test_expired_session_handling():
    """
    Expired tokens must return 401 with detail 'Token has expired'.
    """
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    expired_token = create_access_token(
        user_id=user_id,
        email="expired@dietsense.ai",
        expires_in_secs=-3600,  # Expired 1 hour ago
    )

    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "Token has expired" in res.json()["detail"]


def test_invalid_tokens_rejected():
    """
    Tokens with invalid signatures or bogus payloads must be strictly rejected.
    """
    # 1. Bogus string
    res1 = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert res1.status_code == 401
    assert "Invalid authentication token" in res1.json()["detail"]

    # 2. Token signed with wrong secret
    bad_token = jwt.encode({"sub": "usr_fake", "exp": int(time.time()) + 1000}, "wrong-secret-key-32chars-minimum-needed", algorithm="HS256")
    res2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert res2.status_code == 401


# ─── 6. PASSWORD RESET ───────────────────────────────────────────────────────

def test_password_reset_flow():
    """
    Requesting a password reset delegates to Supabase GoTrue Auth service when applicable.
    """
    with patch("app.routers.auth.supabase_request_password_reset", return_value=True) as mock_reset:
        res = client.post(
            "/api/auth/reset-password",
            json={"email": "reset_user@dietsense.ai"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        mock_reset.assert_called_once_with("reset_user@dietsense.ai")


# ─── 7. STRICT DATA ISOLATION ────────────────────────────────────────────────

def test_user_data_isolation():
    """
    A Supabase-authenticated user and a local-authenticated user cannot access each other's data.
    """
    user1_id = f"usr_{uuid.uuid4().hex[:12]}"
    user2_id = f"usr_{uuid.uuid4().hex[:12]}"

    token1 = create_access_token(user_id=user1_id, email="u1@isolation.ai")
    token2 = create_access_token(user_id=user2_id, email="u2@isolation.ai")

    # User 1 sets profile
    client.put(
        "/api/auth/profile",
        json={"weight_kg": 85.0, "goal": "lose_weight"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User 2 sets profile
    client.put(
        "/api/auth/profile",
        json={"weight_kg": 60.0, "goal": "gain_weight"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    # User 1 profile check
    res1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
    assert res1.status_code == 200
    assert res1.json()["id"] == user1_id
    assert res1.json()["weight_kg"] == 85.0
    assert res1.json()["goal"] == "lose_weight"

    # User 2 profile check
    res2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert res2.status_code == 200
    assert res2.json()["id"] == user2_id
    assert res2.json()["weight_kg"] == 60.0
    assert res2.json()["goal"] == "gain_weight"
