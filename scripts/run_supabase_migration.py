"""
Run DietSense PostgreSQL schema migrations on Supabase.

Reads SUPABASE_DB_URL from backend/.env and executes migration SQL files
using a direct psycopg2 connection (bypasses PostgREST / RLS).

Usage:
    python scripts/run_supabase_migration.py [--file PATH] [--all] [--dry-run]
"""

import sys
import os
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, "backend", ".env")
MIGRATIONS_DIR = os.path.join(ROOT, "backend", "db", "migrations")
SCHEMA_PATH = os.path.join(ROOT, "backend", "db", "schema.sql")


def load_env(path: str) -> dict:
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def execute_sql_file(conn, file_path: str, dry_run: bool = False):
    with open(file_path, encoding="utf-8-sig") as f:
        sql = f.read()

    rel_name = os.path.relpath(file_path, ROOT)
    if dry_run:
        print(f"\n[DRY RUN] Would execute: {rel_name} ({len(sql)} chars)")
        print(sql[:300] + "...")
        return True

    print(f"\nExecuting migration: {rel_name}...")
    try:
        cur = conn.cursor()
        cur.execute(sql)
        print(f"  OK - {rel_name} completed.")
        return True
    except Exception as e:
        print(f"  ERROR executing {rel_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Supabase migrations")
    parser.add_argument("--file", help="Specific migration file to run")
    parser.add_argument("--all", action="store_true", help="Run all migrations in order")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    db_url = env.get("SUPABASE_DB_URL", "")
    if not db_url:
        print("ERROR: SUPABASE_DB_URL not set in backend/.env")
        sys.exit(1)

    # Determine files to execute
    files_to_run = []
    if args.file:
        target = os.path.abspath(args.file) if os.path.isabs(args.file) else os.path.join(ROOT, args.file)
        if not os.path.exists(target):
            print(f"ERROR: File not found: {target}")
            sys.exit(1)
        files_to_run.append(target)
    elif args.all:
        # Schema first, then migrations in alphanumeric order
        if os.path.exists(SCHEMA_PATH):
            files_to_run.append(SCHEMA_PATH)
        if os.path.exists(MIGRATIONS_DIR):
            for fname in sorted(os.listdir(MIGRATIONS_DIR)):
                if fname.endswith(".sql"):
                    files_to_run.append(os.path.join(MIGRATIONS_DIR, fname))
    else:
        # Default: 003_app_tables.sql if exists, otherwise schema.sql
        app_tables = os.path.join(MIGRATIONS_DIR, "003_app_tables.sql")
        if os.path.exists(app_tables):
            files_to_run.append(app_tables)
        else:
            files_to_run.append(SCHEMA_PATH)

    print(f"Target DB: {db_url[:50]}...")
    print(f"Files to execute ({len(files_to_run)}): {[os.path.basename(f) for f in files_to_run]}")

    if args.dry_run:
        for f in files_to_run:
            execute_sql_file(None, f, dry_run=True)
        return

    import psycopg2
    conn = psycopg2.connect(db_url, connect_timeout=15)
    conn.autocommit = True

    success = True
    for f in files_to_run:
        ok = execute_sql_file(conn, f, dry_run=False)
        if not ok:
            success = False
            break

    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name;"
    )
    tables = [row[0] for row in cur.fetchall()]
    print(f"\nTables in public schema ({len(tables)}): {tables}")
    conn.close()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
