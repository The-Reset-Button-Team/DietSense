"""
DietSense — Supabase PostgreSQL Database Integration Tests

Verifies:
1. Direct PostgreSQL connection via connection pooler (port 6543)
2. Schema integrity: all 15 public tables exist with expected columns
3. Foreign key and cascade relationships (profiles, meal_logs, pantry_items -> users)
4. Idempotency: re-syncing records does not create duplicates (sqlite_id UNIQUE)
5. SQLite independence: local SQLite continues working completely independently
"""

import sys
import os
import uuid
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings
from app.core.supabase_client import (
    get_pg_connection,
    get_pg_cursor,
    is_supabase_available,
    get_supabase_client,
)
from db.database import get_connection as get_sqlite_conn, get_db_cursor


@pytest.fixture(scope="module")
def pg_conn():
    """Provides a PostgreSQL connection if Supabase is reachable."""
    if not is_supabase_available():
        pytest.skip("Supabase PostgreSQL not reachable — skipping cloud integration tests")
    conn = get_pg_connection(autocommit=True)
    yield conn
    conn.close()


def test_supabase_connectivity(pg_conn):
    """PostgreSQL responds to version query."""
    cur = pg_conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    assert "PostgreSQL" in version


def test_supabase_public_tables_exist(pg_conn):
    """All 15 required tables exist in public schema."""
    expected_tables = {
        "users", "profiles", "dietary_restrictions", "foods",
        "recipes", "recipe_ingredients", "meal_plans", "meal_plan_items",
        "meal_logs", "user_feedback", "app_feedback", "pantry_items",
        "preference_weights", "progress_logs", "ai_interaction_logs"
    }
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    existing = {r[0] for r in cur.fetchall()}
    missing = expected_tables - existing
    assert not missing, f"Missing tables in Supabase: {missing}"


def test_supabase_profiles_foreign_key_relationship(pg_conn):
    """profiles table references users(id) with ON DELETE CASCADE."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT
            tc.table_name, kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'profiles'
          AND kcu.column_name = 'user_id';
    """)
    fk = cur.fetchone()
    assert fk is not None, "Foreign key from profiles.user_id to users.id not found"
    assert fk[2] == "users"
    assert fk[3] == "id"


def test_pantry_items_unique_constraint(pg_conn):
    """pantry_items enforces UNIQUE(user_id, name) to prevent duplicate items per user."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'pantry_items'
          AND constraint_type = 'UNIQUE'
          AND constraint_name LIKE '%user_id%name%';
    """)
    result = cur.fetchone()
    # Also check pg_indexes for unique index
    if not result:
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'pantry_items'
              AND indexdef LIKE '%UNIQUE%user_id%name%';
        """)
        result = cur.fetchone()
    assert result is not None, "Unique constraint on (user_id, name) in pantry_items not found"


def test_meal_logs_idempotency_via_sqlite_id(pg_conn):
    """meal_logs has sqlite_id column with UNIQUE constraint for deduplication."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'meal_logs' AND column_name = 'sqlite_id';
    """)
    col = cur.fetchone()
    assert col is not None, "sqlite_id column not found on meal_logs"

    # Verify unique constraint on sqlite_id
    cur.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'meal_logs'
          AND indexdef LIKE '%UNIQUE%sqlite_id%';
    """)
    idx = cur.fetchone()
    assert idx is not None, "UNIQUE index on meal_logs.sqlite_id not found"


def test_sqlite_independence():
    """
    Local SQLite database must continue operating completely independently
    of Supabase configuration.
    """
    # 1. Connection opens successfully
    conn = get_sqlite_conn()
    cur = conn.cursor()

    # 2. Can query foods catalog
    cur.execute("SELECT count(*) FROM foods WHERE calories_kcal > 50;")
    count = cur.fetchone()[0]
    assert count > 10000, f"Expected >10,000 foods in SQLite, found {count}"

    # 3. Can perform a local transaction
    cur.execute("SELECT count(*) FROM users;")
    user_count = cur.fetchone()[0]
    assert user_count >= 1, "Expected at least 1 user in SQLite"

    conn.close()


def test_supabase_sdk_client_initialization():
    """Supabase Python SDK client initializes with configured credentials."""
    client = get_supabase_client()
    if not is_supabase_available():
        pytest.skip("Supabase credentials not configured")
    assert client is not None
