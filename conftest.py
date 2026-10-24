"""
DietSense — Root conftest.py
Ensures the repo root and backend/ are on sys.path for all tests,
so that `from app.* import ...` and `from ml.* import ...` work
regardless of which directory pytest is launched from.
"""
import sys
import os

# Repo root → provides: ml/, routes/, scripts/, data/, database/
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# backend/ → provides: app/ (FastAPI app, routers, schemas, core)
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
