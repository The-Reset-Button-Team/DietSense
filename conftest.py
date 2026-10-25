"""
DietSense — Root conftest.py
Ensures the repo root and backend/ are on sys.path for all tests,
and provisions an isolated temporary SQLite database for test runs.
"""
import sys
import os
import shutil
import tempfile
import pytest

# Repo root → provides: ml/, routes/, scripts/, data/, database/
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# backend/ → provides: app/ (FastAPI app, routers, schemas, core)
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    """
    Creates an isolated temporary copy of the SQLite database for tests,
    preserving the production food catalog without polluting user data.
    """
    from app.core.config import settings
    from db.database import init_db

    prod_db = os.path.join(_ROOT, "database", "dietsense.db")
    temp_dir = tempfile.mkdtemp()
    test_db = os.path.join(temp_dir, "test_dietsense.db")

    if os.path.exists(prod_db):
        shutil.copy2(prod_db, test_db)

    original_path = settings.sqlite_db_path
    settings.sqlite_db_path = test_db
    init_db(test_db)

    yield

    settings.sqlite_db_path = original_path
    shutil.rmtree(temp_dir, ignore_errors=True)
