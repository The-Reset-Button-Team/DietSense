"""
DietSense — Supabase Client Module

Provides a singleton Supabase client for backend-only server operations.
Uses the service role key (sb_secret_*) which bypasses RLS — this module
must NEVER be imported in frontend code.

Configuration is loaded from backend/.env via pydantic-settings.
"""

import os
from functools import lru_cache
from typing import Optional

import psycopg2
import psycopg2.extras

from app.core.config import settings


# ─── Supabase REST SDK Client ─────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_supabase_client():
    """
    Returns a cached Supabase Python SDK client using the service role key.
    Returns None if Supabase credentials are not configured.
    """
    url = getattr(settings, "supabase_url", "") or ""
    key = getattr(settings, "supabase_service_role_key", "") or ""

    if not url or not key or key.startswith("[YOUR"):
        return None

    try:
        from supabase import create_client, Client
        client: Client = create_client(url, key)
        return client
    except Exception as e:
        print(f"[supabase_client] Failed to create Supabase client: {e}")
        return None


# ─── Direct PostgreSQL Connection ──────────────────────────────────────────────

def get_pg_connection(autocommit: bool = False):
    """
    Returns a direct psycopg2 connection to Supabase PostgreSQL.
    Uses the pooler URL (port 6543, transaction mode).
    Returns None if the DB URL is not configured.

    Caller is responsible for closing the connection.
    """
    db_url = getattr(settings, "supabase_db_url", "") or ""
    if not db_url:
        # Try to read from env directly
        db_url = os.environ.get("SUPABASE_DB_URL", "")

    if not db_url:
        return None

    try:
        conn = psycopg2.connect(db_url, connect_timeout=15)
        conn.autocommit = autocommit
        return conn
    except Exception as e:
        print(f"[supabase_client] PostgreSQL connection failed: {e}")
        return None


def get_pg_cursor(conn=None):
    """
    Returns a RealDictCursor from a PostgreSQL connection.
    If no connection is provided, creates a new one.
    """
    if conn is None:
        conn = get_pg_connection()
    if conn is None:
        return None, None
    return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ─── Database Provider Detection ──────────────────────────────────────────────

def get_database_provider() -> str:
    """
    Returns the active database provider: 'supabase' or 'sqlite'.
    Reads DATABASE_PROVIDER from settings or env (default: 'sqlite').
    """
    provider = (
        getattr(settings, "database_provider", "")
        or os.environ.get("DATABASE_PROVIDER", "sqlite")
    ).strip().lower()

    if provider == "supabase":
        # Verify we can actually connect
        conn = get_pg_connection()
        if conn:
            conn.close()
            return "supabase"
        else:
            print("[supabase_client] DATABASE_PROVIDER=supabase but connection failed. Falling back to sqlite.")
            return "sqlite"
    return "sqlite"


def is_supabase_available() -> bool:
    """Quick check: can we reach Supabase PostgreSQL?"""
    try:
        conn = get_pg_connection()
        if conn:
            conn.close()
            return True
    except Exception:
        pass
    return False
