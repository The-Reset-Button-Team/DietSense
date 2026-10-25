"""
DietSense — Database Client
Manages local SQLite database connections and sessions.
"""

from typing import Any, Optional
import sqlite3
from db.database import get_connection, get_db_cursor, get_db_path


def get_db_client() -> sqlite3.Connection:
    """Initialize and return the SQLite database connection."""
    return get_connection()


def get_db_session():
    """Dependency generator for FastAPI routes to obtain a SQLite database session."""
    with get_db_cursor() as cur:
        yield cur
