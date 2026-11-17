"""
DietSense — Migration 005: Synchronization Queue & Conflict Resolution Tables
Creates:
- SQLite `sync_queue` table for pending mutations with retry and exponential backoff tracking.
- SQLite `sync_metadata` table for sync status, last-synced timestamp, and error reporting.
- Metadata columns (`synced_at`, `updated_at`) across operational tables for conflict resolution.
- Mirrors sync metadata columns on Supabase PostgreSQL (sqlite_id UNIQUE, synced_at).
"""

import sys
import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db.database import get_db_cursor
from app.core.supabase_client import get_pg_connection


def migrate_sqlite():
    print("Migrating SQLite schema for sync support...")
    with get_db_cursor() as cur:
        # 1. sync_queue
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

        # 2. sync_metadata
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

        # 3. Add synced_at and updated_at columns to local operational tables
        tables_to_augment = [
            ("profiles", ["synced_at TEXT"]),
            ("meal_plans", ["synced_at TEXT", "updated_at TEXT"]),
            ("meal_logs", ["synced_at TEXT", "updated_at TEXT"]),
            ("feedback", ["synced_at TEXT", "updated_at TEXT"]),
            ("pantry_items", ["synced_at TEXT"]),
        ]

        for table, new_cols in tables_to_augment:
            cur.execute(f"PRAGMA table_info({table});")
            existing = [row["name"] for row in cur.fetchall()]
            for col_def in new_cols:
                col_name = col_def.split()[0]
                if col_name not in existing:
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def};")
                        print(f"Added {col_name} to {table}")
                    except Exception as e:
                        print(f"Notice adding {col_name} to {table}: {e}")

        # Populate updated_at from created_at if null
        try:
            cur.execute("UPDATE meal_plans SET updated_at = created_at WHERE updated_at IS NULL;")
            cur.execute("UPDATE meal_logs SET updated_at = created_at WHERE updated_at IS NULL;")
            cur.execute("UPDATE feedback SET updated_at = created_at WHERE updated_at IS NULL;")
        except Exception:
            pass

    print("SQLite sync tables initialized successfully.")


def migrate_postgres():
    print("Checking Supabase PostgreSQL schema for sync columns...")
    pg = get_pg_connection(autocommit=True)
    if not pg:
        print("Supabase PostgreSQL not connected/reachable. Skipping Postgres sync column additions.")
        return

    try:
        cur = pg.cursor()
        # 1. meal_plans
        cur.execute("ALTER TABLE public.meal_plans ADD COLUMN IF NOT EXISTS sqlite_id TEXT UNIQUE;")
        cur.execute("ALTER TABLE public.meal_plans ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;")
        cur.execute("ALTER TABLE public.meal_plans ADD COLUMN IF NOT EXISTS items JSONB DEFAULT '[]'::JSONB;")

        # 2. profiles
        cur.execute("ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS sqlite_id TEXT;")
        cur.execute("ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;")

        # 3. meal_logs
        cur.execute("ALTER TABLE public.meal_logs ADD COLUMN IF NOT EXISTS sqlite_id TEXT UNIQUE;")
        cur.execute("ALTER TABLE public.meal_logs ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;")

        # 4. pantry_items
        cur.execute("ALTER TABLE public.pantry_items ADD COLUMN IF NOT EXISTS sqlite_id TEXT UNIQUE;")
        cur.execute("ALTER TABLE public.pantry_items ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;")

        # 5. app_feedback
        cur.execute("ALTER TABLE public.app_feedback ADD COLUMN IF NOT EXISTS sqlite_id TEXT UNIQUE;")
        cur.execute("ALTER TABLE public.app_feedback ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;")

        print("Supabase PostgreSQL sync columns verified/added successfully.")
    except Exception as e:
        print(f"Supabase PostgreSQL sync migration notice: {e}")
    finally:
        pg.close()


if __name__ == "__main__":
    migrate_sqlite()
    migrate_postgres()
