"""
DietSense — Database Initialization CLI
Run this script to initialize or verify SQLite schema without deleting data:
    python backend/db/init_db.py
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db.database import init_db, get_db_path, get_connection

def main():
    path = get_db_path()
    print(f"Initializing DietSense SQLite database at:\n  {path}")
    init_db(path)
    conn = get_connection(path)
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    print(f"Database initialization successful! Active tables: {', '.join(sorted(tables))}")

if __name__ == "__main__":
    main()
