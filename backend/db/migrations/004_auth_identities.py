"""
DietSense — Migration 004: Auth Identities
Adds the auth_identities table to SQLite and Supabase PostgreSQL (if available)
and backfills existing local users into auth_identities.
"""

import sys
import os
import uuid
from datetime import datetime, timezone

# Add backend and root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db.database import get_connection, get_db_cursor
from app.core.supabase_client import get_pg_connection

def migrate_sqlite():
    print("Migrating SQLite database...")
    with get_db_cursor() as cur:
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

        # Backfill existing local users
        cur.execute("SELECT id, email, created_at, updated_at FROM users")
        users = cur.fetchall()
        backfilled = 0
        for u in users:
            uid = u["id"]
            email = u["email"]
            c_at = u["created_at"] or datetime.now(timezone.utc).isoformat()
            u_at = u["updated_at"] or c_at
            
            # Check if identity exists
            cur.execute(
                "SELECT id FROM auth_identities WHERE provider = 'local' AND provider_user_id = ?",
                (uid,)
            )
            if not cur.fetchone():
                ident_id = f"ident_{uuid.uuid4().hex[:12]}"
                cur.execute(
                    """
                    INSERT INTO auth_identities (id, user_id, provider, provider_user_id, email, created_at, updated_at)
                    VALUES (?, ?, 'local', ?, ?, ?, ?)
                    """,
                    (ident_id, uid, uid, email, c_at, u_at)
                )
                backfilled += 1
        print(f"SQLite migration complete. Backfilled {backfilled} existing local users.")

def migrate_postgres():
    print("Checking Supabase PostgreSQL connection...")
    pg = get_pg_connection(autocommit=True)
    if not pg:
        print("Supabase PostgreSQL not connected/reachable. Skipping Postgres table creation.")
        return
    try:
        cur = pg.cursor()
        # Check users id column type
        cur.execute("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'id';
        """)
        row = cur.fetchone()
        user_id_type = row[0] if row else "text"
        print(f"Postgres public.users.id type is: {user_id_type}")

        if user_id_type.lower() == "uuid":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.auth_identities (
                    id TEXT PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                    provider TEXT NOT NULL,
                    provider_user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(provider, provider_user_id)
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.auth_identities (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                    provider TEXT NOT NULL,
                    provider_user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(provider, provider_user_id)
                );
            """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pg_identities_user_id ON public.auth_identities(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pg_identities_provider_email ON public.auth_identities(provider, email);")
        print("Supabase PostgreSQL auth_identities table created successfully.")
    except Exception as e:
        print(f"Supabase PostgreSQL migration notice: {e}")
    finally:
        pg.close()

if __name__ == "__main__":
    migrate_sqlite()
    migrate_postgres()
