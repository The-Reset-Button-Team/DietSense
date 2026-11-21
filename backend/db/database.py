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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pantry_items_matched_food ON pantry_items(user_id, matched_food_id);")

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

        # 10. Food Prices table (Separate Indian food pricing model connected to foods catalog)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS food_prices (
                price_id TEXT PRIMARY KEY,
                food_id INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
                price REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'INR',
                unit TEXT NOT NULL,
                region TEXT NOT NULL DEFAULT 'National',
                source TEXT NOT NULL,
                price_type TEXT NOT NULL CHECK (price_type IN ('verified', 'estimated')),
                last_updated TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_food_prices_food_id ON food_prices(food_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_food_prices_region ON food_prices(region);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_food_prices_type ON food_prices(price_type);")

        # 11. Daily Featured Foods table (Food of the Day persistence and deterministic calendar tracking)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_featured_foods (
                feature_date TEXT PRIMARY KEY,
                food_id INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
                short_intro TEXT,
                description TEXT,
                common_usage TEXT,
                preparation_methods TEXT,
                image_url TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_featured_food_id ON daily_featured_foods(food_id);")

        _seed_food_prices_if_empty(cur)


def _seed_food_prices_if_empty(cur: sqlite3.Cursor) -> None:
    """Populates initial Indian food pricing benchmark data if food_prices is empty."""
    cur.execute("SELECT COUNT(*) AS cnt FROM food_prices")
    if cur.fetchone()["cnt"] > 0:
        return

    # Check that foods table exists and has rows before inserting foreign keys
    cur.execute("SELECT COUNT(*) AS cnt FROM foods")
    if cur.fetchone()["cnt"] == 0:
        return

    sample_prices = [
        # Wheat flour, atta (food_id: 16) - Verified DoCA
        ("prc_atta_nat", 16, 36.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_atta_del", 16, 35.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_atta_mum", 16, 38.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_atta_blr", 16, 40.0, "INR", "kg", "Bengaluru", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_atta_kol", 16, 37.0, "INR", "kg", "Kolkata", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Rice, raw, brown (food_id: 10)
        ("prc_rice_brn_nat", 10, 52.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Rice, parboiled (food_id: 11)
        ("prc_rice_par_nat", 11, 40.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Rice, raw, milled (food_id: 12)
        ("prc_rice_mil_nat", 12, 44.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_rice_mil_del", 12, 42.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_rice_mil_mum", 12, 46.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_rice_mil_kol", 12, 41.0, "INR", "kg", "Kolkata", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Bengal gram, dal / Chana dal (food_id: 22)
        ("prc_chana_nat", 22, 88.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_chana_del", 22, 85.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_chana_mum", 22, 90.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Black gram, dal / Urad dal (food_id: 24)
        ("prc_urad_nat", 24, 125.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Green gram, dal / Moong dal (food_id: 31)
        ("prc_moong_nat", 31, 112.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_moong_del", 31, 110.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_moong_blr", 31, 118.0, "INR", "kg", "Bengaluru", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Lentil dal / Masoor dal (food_id: 34)
        ("prc_masoor_nat", 34, 94.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Rajmah, red (food_id: 41)
        ("prc_rajmah_nat", 41, 145.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Potato, brown skin (food_id: 205)
        ("prc_potato_nat", 205, 28.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_potato_del", 205, 25.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_potato_mum", 205, 30.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_potato_kol", 205, 26.0, "INR", "kg", "Kolkata", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Onion, big (food_id: 235)
        ("prc_onion_nat", 235, 32.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_onion_del", 235, 30.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_onion_mum", 235, 28.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_onion_blr", 235, 34.0, "INR", "kg", "Bengaluru", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Tomato, ripe, local (food_id: 131)
        ("prc_tomato_nat", 131, 38.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_tomato_del", 131, 35.0, "INR", "kg", "Delhi", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_tomato_mum", 131, 42.0, "INR", "kg", "Mumbai", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_tomato_blr", 131, 32.0, "INR", "kg", "Bengaluru", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Tomato, ripe, hybrid (food_id: 130)
        ("prc_tomato_hyb_nat", 130, 42.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Milk, whole, Cow (food_id: 282)
        ("prc_cow_milk_nat", 282, 58.0, "INR", "litre", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),
        ("prc_cow_milk_del", 282, 56.0, "INR", "litre", "Delhi", "Mother Dairy / DoCA Price Cell", "verified", "2026-05-15"),
        ("prc_cow_milk_mum", 282, 60.0, "INR", "litre", "Mumbai", "Amul / DoCA Price Cell", "verified", "2026-05-15"),
        ("prc_cow_milk_blr", 282, 48.0, "INR", "litre", "Bengaluru", "Nandini (KMF) / DoCA Price Cell", "verified", "2026-05-15"),

        # Milk, whole, Buffalo (food_id: 281)
        ("prc_buf_milk_nat", 281, 70.0, "INR", "litre", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Paneer (food_id: 283) - Estimated retail index
        ("prc_paneer_nat", 283, 420.0, "INR", "kg", "National", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),
        ("prc_paneer_del", 283, 400.0, "INR", "kg", "Delhi", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),
        ("prc_paneer_mum", 283, 440.0, "INR", "kg", "Mumbai", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),

        # Egg, poultry, whole, raw (food_id: 284)
        ("prc_egg_piece_nat", 284, 7.0, "INR", "piece", "National", "National Egg Coordination Committee (NECC)", "verified", "2026-05-15"),
        ("prc_egg_doz_del", 284, 84.0, "INR", "dozen", "Delhi", "National Egg Coordination Committee (NECC)", "verified", "2026-05-15"),
        ("prc_egg_doz_mum", 284, 86.0, "INR", "dozen", "Mumbai", "National Egg Coordination Committee (NECC)", "verified", "2026-05-15"),

        # Chicken, breast, skinless (food_id: 301)
        ("prc_chicken_nat", 301, 290.0, "INR", "kg", "National", "Retail Poultry Market Index", "estimated", "2026-05-15"),
        ("prc_chicken_del", 301, 280.0, "INR", "kg", "Delhi", "Retail Poultry Market Index", "estimated", "2026-05-15"),
        ("prc_chicken_blr", 301, 310.0, "INR", "kg", "Bengaluru", "Retail Poultry Market Index", "estimated", "2026-05-15"),

        # Goat, shoulder / Mutton (food_id: 318)
        ("prc_goat_nat", 318, 780.0, "INR", "kg", "National", "Retail Meat Market Index", "estimated", "2026-05-15"),

        # Tiger prawns, brown (food_id: 479)
        ("prc_prawn_nat", 479, 480.0, "INR", "kg", "National", "Coastal Fisheries Market Index", "estimated", "2026-05-15"),

        # Spinach (food_id: 69)
        ("prc_spinach_nat", 69, 30.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),
        ("prc_spinach_del", 69, 25.0, "INR", "kg", "Delhi", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Cauliflower (food_id: 94)
        ("prc_cauli_nat", 94, 35.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Cabbage, Chinese (food_id: 55)
        ("prc_cabbage_nat", 55, 40.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Chillies, green (food_id: 219)
        ("prc_chilli_nat", 219, 80.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Turmeric powder (food_id: 251)
        ("prc_turmeric_nat", 251, 26.0, "INR", "100g", "National", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),

        # Jaggery, cane (food_id: 273)
        ("prc_jaggery_nat", 273, 55.0, "INR", "kg", "National", "Department of Consumer Affairs (DoCA), Govt of India", "verified", "2026-05-15"),

        # Almond (food_id: 252)
        ("prc_almond_nat", 252, 85.0, "INR", "100g", "National", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),

        # Cashew nut (food_id: 256)
        ("prc_cashew_nat", 256, 98.0, "INR", "100g", "National", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),

        # Walnut (food_id: 272)
        ("prc_walnut_nat", 272, 125.0, "INR", "100g", "National", "Curated Indian Retail Market Index", "estimated", "2026-05-15"),

        # Ground nut (food_id: 263)
        ("prc_groundnut_nat", 263, 140.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Bajra (food_id: 2)
        ("prc_bajra_nat", 2, 27.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Jowar (food_id: 4)
        ("prc_jowar_nat", 4, 42.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Ragi (food_id: 8)
        ("prc_ragi_nat", 8, 38.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Barley (food_id: 3)
        ("prc_barley_nat", 3, 34.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Apple, big (food_id: 134)
        ("prc_apple_nat", 134, 140.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),
        ("prc_apple_del", 134, 130.0, "INR", "kg", "Delhi", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Apple, small, Kashmir (food_id: 137)
        ("prc_apple_ksh_nat", 137, 110.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Banana, ripe, montham (food_id: 142)
        ("prc_banana_doz_nat", 142, 48.0, "INR", "dozen", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),

        # Banana, ripe, robusta (food_id: 145)
        ("prc_banana_kg_nat", 145, 45.0, "INR", "kg", "National", "Agmarknet Daily Market Index", "verified", "2026-05-15"),
        ("prc_banana_kg_blr", 145, 35.0, "INR", "kg", "Bengaluru", "Agmarknet Daily Market Index", "verified", "2026-05-15"),
    ]

    cur.executemany(
        """
        INSERT OR IGNORE INTO food_prices (
            price_id, food_id, price, currency, unit, region, source, price_type, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample_prices,
    )
