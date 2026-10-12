"""
DietSense — Authentication & Authorization Tests
Verifies Supabase JWT token validation, 401/403 responses, and user-level data isolation.
"""

import sys
import os
import time
import jwt
import pytest
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

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(
    user_id: str,
    email: str = "test@dietsense.ai",
    expires_in_secs: int = 3600,
    audience: str = TEST_AUDIENCE,
    secret: str = TEST_SECRET,
    role: str = "authenticated",
) -> str:
    """Helper to generate standard Supabase-format JWTs for testing."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": audience,
        "role": role,
        "exp": int(time.time()) + expires_in_secs,
        "iat": int(time.time()),
        "user_metadata": {
            "full_name": f"User {user_id[:6]}",
        },
    }
    return jwt.encode(payload, secret, algorithm=TEST_ALGORITHM)


def test_auth_missing_token_returns_401():
    """Protected endpoints return 401 when Authorization header is absent."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["detail"]


def test_auth_malformed_token_returns_401():
    """Protected endpoints return 401 when token is malformed."""
    headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


def test_auth_invalid_signature_returns_401():
    """Token signed with wrong secret is rejected with 401."""
    token = generate_token("user-123", secret="wrong-secret-key")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_expired_token_returns_401():
    """Expired token is rejected with 401 and specific expiry notice."""
    token = generate_token("user-123", expires_in_secs=-100)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


def test_auth_invalid_audience_returns_401():
    """Token with wrong audience claim is rejected with 401."""
    token = generate_token("user-123", audience="wrong-aud")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Invalid token audience" in response.json()["detail"]


def test_auth_valid_token_succeeds():
    """Valid token allows access and correctly identifies the user."""
    user_id = "usr_00000000-0000-0000-0000-000000000001"
    token = generate_token(user_id=user_id, email="alice@dietsense.ai")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "alice@dietsense.ai"


def test_user_isolation_cannot_read_or_modify_other_user():
    """
    User A cannot read or modify User B's profile or meal logs.
    Enforces user-level isolation where user ID is extracted solely from token.
    """
    user_a_id = "usr_aaaa1111-0000-0000-0000-00000000000a"
    user_b_id = "usr_bbbb2222-0000-0000-0000-00000000000b"

    token_a = generate_token(user_id=user_a_id, email="user_a@dietsense.ai")
    token_b = generate_token(user_id=user_b_id, email="user_b@dietsense.ai")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A sets their profile
    res_update_a = client.post(
        "/users/profile",
        json={"dietary_pref": "vegan", "budget_per_meal": 250},
        headers=headers_a,
    )
    assert res_update_a.status_code == 200
    assert res_update_a.json()["id"] == user_a_id
    assert res_update_a.json()["dietary_pref"] == "vegan"

    # 2. User B requests their profile
    res_get_b = client.get("/users/profile", headers=headers_b)
    assert res_get_b.status_code == 200
    # Must be User B, not User A
    assert res_get_b.json()["id"] == user_b_id
    assert res_get_b.json()["email"] == "user_b@dietsense.ai"
    assert res_get_b.json()["dietary_pref"] != "vegan"

    # 3. User A logs feedback
    client.post(
        "/feedback/",
        json={"meal_id": 101, "status": "skipped", "reason": "time"},
        headers=headers_a,
    )

    # 4. User B queries feedback
    res_feedback_b = client.get("/feedback/", headers=headers_b)
    assert res_feedback_b.status_code == 200
    feedback_b = res_feedback_b.json()
    # User B should not see User A's feedback
    for entry in feedback_b:
        assert entry["user_id"] == user_b_id
        assert entry["user_id"] != user_a_id
