"""
DietSense — Local Authentication & SQLite Database Persistence Tests
Comprehensive automated verification for:
- Local registration, login, logout, password hashing, and cookie sessions
- Duplicate registration rejection and invalid credentials
- Strict user data isolation (profiles, plans, logs, feedback)
- SQLite database initialization, idempotency, foreign key enforcement
- Adaptive feedback affecting recommendations
"""

import os
import sys
import time
import uuid
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, verify_password, normalize_email
from db.database import init_db, get_connection, get_db_cursor

client = TestClient(app)


def test_password_hashing_and_verification():
    """Verify bcrypt hashes passwords, never stores plaintext, and verifies correctly."""
    raw_pass = "MySecretPassw0rd!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert hashed.startswith("$2b$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_email_normalization():
    """Verify email normalization trims whitespace and lowercases."""
    assert normalize_email("  Test.User@Example.COM  ") == "test.user@example.com"
    assert normalize_email("") == ""


def test_database_idempotent_init():
    """Verify init_db can be called repeatedly without duplicating tables or failing."""
    init_db()
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert "users" in tables
    assert "profiles" in tables
    assert "meal_plans" in tables
    assert "meal_logs" in tables
    assert "feedback" in tables
    assert "foods" in tables


def test_foreign_key_enforcement():
    """Verify SQLite foreign key enforcement rejects orphaned records."""
    conn = get_connection()
    cur = conn.cursor()
    random_user_id = f"nonexistent_{uuid.uuid4().hex}"
    with pytest.raises(Exception):
        cur.execute(
            """
            INSERT INTO meal_plans (id, user_id, date, target_calories, items, status, created_at)
            VALUES ('plan_orphan', ?, '2026-10-24', 2000, '[]', 'generated', '2026-10-24T00:00:00Z')
            """,
            (random_user_id,),
        )
    conn.close()


def test_local_registration_and_login_flow():
    """Verify complete registration, cookie issuance, profile fetch, and login."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@localtest.ai"
    password = "SecurePassword123!"

    # 1. Register new user
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Test Local User",
            "age": 28,
            "gender": "female",
            "height_cm": 165.0,
            "weight_kg": 60.0,
            "goal": "maintain_weight",
            "activity_level": "moderately_active",
        },
    )
    assert reg_res.status_code == 200
    user_data = reg_res.json()
    assert user_data["email"] == unique_email.lower()
    assert user_data["full_name"] == "Test Local User"
    assert user_data["token"] is not None
    user_id = user_data["id"]

    # Verify session cookie was set
    assert settings.session_cookie_name in reg_res.cookies

    # 2. Duplicate registration rejection
    dup_res = client.post(
        "/api/auth/register",
        json={
            "email": unique_email.upper(),  # Check case-insensitive rejection
            "password": "AnotherPassword123!",
            "full_name": "Duplicate User",
        },
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Invalid login credentials
    bad_login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login_res.status_code == 401
    assert "Invalid email or password" in bad_login_res.json()["detail"]

    # 4. Successful login
    login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["id"] == user_id
    assert settings.session_cookie_name in login_res.cookies

    # 5. Authenticated /api/auth/me using Cookie
    cookie_value = login_res.cookies[settings.session_cookie_name]
    me_res = client.get("/api/auth/me", cookies={settings.session_cookie_name: cookie_value})
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id
    assert me_res.json()["email"] == unique_email.lower()

    # 6. Logout clears session cookie
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    # Cookie should be cleared / expired
    set_cookie = logout_res.headers.get("set-cookie", "")
    assert settings.session_cookie_name in set_cookie


def test_user_data_isolation_across_endpoints():
    """Verify User A and User B cannot read or modify each other's profiles, meal plans, or logs."""
    email_a = f"usera_{uuid.uuid4().hex[:8]}@isolation.ai"
    email_b = f"userb_{uuid.uuid4().hex[:8]}@isolation.ai"
    pwd = "IsolationPassword123!"

    # Register User A
    res_a = client.post("/api/auth/register", json={"email": email_a, "password": pwd, "full_name": "Alice"})
    token_a = res_a.json()["token"]
    user_a_id = res_a.json()["id"]

    # Register User B
    res_b = client.post("/api/auth/register", json={"email": email_b, "password": pwd, "full_name": "Bob"})
    token_b = res_b.json()["token"]
    user_b_id = res_b.json()["id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A updates profile constraints
    client.put(
        "/profile",
        json={"dietary_pref": "vegan", "budget_per_meal": 220, "allergies": ["peanuts"]},
        headers=headers_a,
    )

    # 2. User B gets profile -> must NOT see User A's data
    prof_b = client.get("/profile", headers=headers_b).json()
    assert prof_b["id"] == user_b_id
    assert prof_b["dietary_pref"] != "vegan"
    assert prof_b["budget_per_meal"] != 220

    # 3. User A creates a meal plan
    plan_res = client.post(
        "/meal-plans",
        json={"date": "2026-10-25", "target_calories": 2100, "items": [{"name": "User A Meal"}]},
        headers=headers_a,
    )
    plan_id_a = plan_res.json()["id"]

    # 4. User B cannot see User A's meal plans in list
    plans_b = client.get("/meal-plans", headers=headers_b).json()
    assert all(p["id"] != plan_id_a for p in plans_b)

    # 5. User B cannot fetch User A's meal plan by ID
    get_plan_b = client.get(f"/meal-plans/{plan_id_a}", headers=headers_b)
    assert get_plan_b.status_code == 404

    # 6. User A logs meal and feedback
    client.post(
        "/meal-logs",
        json={"meal_id": "meal_123", "status": "skipped", "reason": "cost"},
        headers=headers_a,
    )

    # 7. User B queries meal logs and analytics -> must have 0 logs
    logs_b = client.get("/meal-logs", headers=headers_b).json()
    assert len(logs_b) == 0

    analytics_b = client.get("/analytics", headers=headers_b).json()
    assert analytics_b["total_logged"] == 0
    assert analytics_b["has_data"] is False


def test_sqlite_persistence_across_connections():
    """Verify that records saved to SQLite persist and can be read by a direct DB query."""
    unique_email = f"persist_{uuid.uuid4().hex[:8]}@dietsense.ai"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "TestPassword123!", "full_name": "Persist User"},
    )
    user_id = reg_res.json()["id"]

    with get_db_cursor() as cur:
        cur.execute("SELECT id, email, full_name, password_hash FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        assert row is not None
        assert row["email"] == unique_email.lower()
        assert row["full_name"] == "Persist User"
        assert row["password_hash"] != "TestPassword123!"


def test_adaptive_feedback_sqlite_integration():
    """Verify that skip reasons recorded in SQLite affect subsequent recommendation scores."""
    unique_email = f"adaptive_{uuid.uuid4().hex[:8]}@dietsense.ai"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "Password123!", "full_name": "Adaptive User"},
    )
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Baseline recommendations
    rec1 = client.post(
        "/recommendations/",
        json={"dietary_pref": "all", "top_n": 10},
        headers=headers,
    ).json()
    assert len(rec1) > 0

    # User logs 3 skips for reason 'time' (triggers 'long-prep-time' penalty)
    for _ in range(3):
        client.post(
            "/meal-logs",
            json={"meal_id": "1", "status": "skipped", "reason": "time", "item_tags": ["long-prep-time"]},
            headers=headers,
        )

    # Subsequent recommendations should include adaptive penalty in breakdown
    rec2 = client.post(
        "/recommendations/",
        json={"dietary_pref": "", "top_n": 50},
        headers=headers,
    ).json()

    # Find meals with long-prep-time penalty applied
    penalized = [r for r in rec2 if r["breakdown"].get("adaptive_penalty", 0) > 0]
    assert len(penalized) > 0
    assert penalized[0]["breakdown"]["adaptive_penalty"] >= 0.1
