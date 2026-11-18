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

        # 1b. Auth Identities table (Maps internal user_id to local & Supabase providers)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_identities (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(provider, provider_user_id)
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_identities_user_id ON auth_identities(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_identities_provider_email ON auth_identities(provider, email);")

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
                synced_at TEXT,
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
                synced_at TEXT,
                updated_at TEXT,
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
                synced_at TEXT,
                updated_at TEXT,
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
                synced_at TEXT,
                updated_at TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);")

        # 6. Pantry Items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pantry_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                quantity TEXT NOT NULL DEFAULT '1 unit',
                in_stock INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'manual',
                expiry_date TEXT,
                matched_food_id INTEGER,
                synced_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pantry_items_user_id ON pantry_items(user_id);")

        try:
            cur.execute("ALTER TABLE pantry_items ADD COLUMN expiry_date TEXT;")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE pantry_items ADD COLUMN matched_food_id INTEGER;")
        except Exception:
            pass

        # 7. Sync Queue table (Pending mutations for cloud sync)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 5,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_user_status ON sync_queue (user_id, status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_entity ON sync_queue (entity_type, entity_id);")

        # 8. Sync Metadata table (User-level sync status & timestamps)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                last_synced_at TEXT,
                last_attempt_at TEXT,
                sync_status TEXT NOT NULL DEFAULT 'idle',
                last_error TEXT,
                pending_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
        """)

        # 9. AI Interaction Logs table (Audit logging for Gemini prompts & responses)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_interaction_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                feature TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_user_id ON ai_interaction_logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_created_at ON ai_interaction_logs(created_at);")
