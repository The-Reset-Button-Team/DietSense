"""
DietSense — FastAPI Application Entrypoint (legacy wrapper)

This file exists for backwards compatibility.
The authoritative entry point is backend/app/main.py.

Run from the REPOSITORY ROOT (not from backend/) so that the ml/ and routes/
packages are importable:

    # From repo root:
    $env:PYTHONPATH = ".;backend"       # PowerShell (Windows)
    uvicorn app.main:app --reload --port 8000

Or use the helper script:
    python run_backend.py
"""

# Re-export the canonical app so `uvicorn backend.main:app` still works
# if someone runs it that way (though the preferred entry is app.main:app)
from app.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
