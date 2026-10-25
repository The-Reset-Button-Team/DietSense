"""
DietSense — Local SQLite Database Architecture
Handles SQLite connection, foreign keys, WAL mode, schema initialization,
and database session management.
"""

import os
import sqlite3
import json
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings

def get_db_path() -> str:
    """Returns absolute path to the local SQLite database."""
    return settings.sqlite_db_path

def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Enforces foreign keys, enables WAL mode, and returns sqlite3.Row rows.
    """
    path = db_path or get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_cursor(db_path: str = None) -> Generator[sqlite3.Cursor, None, None]:
    """Context manager yielding a database cursor within a transaction."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path: str = None) -> None:
    """
    Idempotent schema initialization.
    Safely creates all application tables if they do not exist.
    Never modifies or deletes existing records in foods or application tables.
    """
    path = db_path or get_db_path()
    with get_db_cursor(path) as cur:
        # 1. Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

        # 2. Profiles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                email TEXT NOT NULL COLLATE NOCASE,
                full_name TEXT NOT NULL DEFAULT '',
                dietary_pref TEXT NOT NULL DEFAULT 'vegetarian',
                allergies TEXT NOT NULL DEFAULT '[]',
                target_calories INTEGER NOT NULL DEFAULT 2000,
                budget_per_meal REAL NOT NULL DEFAULT 100.0,
                prep_time_limit INTEGER NOT NULL DEFAULT 30,
                is_solo_cook INTEGER NOT NULL DEFAULT 1,
                active_meal_frequency TEXT NOT NULL DEFAULT '3_meals',
                age INTEGER NOT NULL DEFAULT 26,
                gender TEXT NOT NULL DEFAULT 'male',
                height_cm REAL NOT NULL DEFAULT 175.0,
                weight_kg REAL NOT NULL DEFAULT 75.0,
                goal TEXT NOT NULL DEFAULT 'lose_weight',
                activity_level TEXT NOT NULL DEFAULT 'lightly_active',
                preferred_cuisines TEXT NOT NULL DEFAULT '["indian"]',
                updated_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);")

        # 3. Meal Plans table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                target_calories INTEGER NOT NULL DEFAULT 2000,
                items TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'generated',
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_meal_plans_user_date ON meal_plans(user_id, date);")

        # 4. Meal Logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meal_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                meal_id TEXT,
                status TEXT NOT NULL CHECK (status IN ('eaten', 'skipped')),
                reason TEXT CHECK (reason IS NULL OR reason IN ('time', 'cost', 'taste', 'unavailable')),
                item_tags TEXT NOT NULL DEFAULT '[]',
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_meal_logs_user_id ON meal_logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_meal_logs_user_time ON meal_logs(user_id, timestamp);")

        # 5. Feedback table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                meal_id TEXT,
                status TEXT NOT NULL,
                reason TEXT,
                feedback_text TEXT,
                derived_penalty_tag TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);")
