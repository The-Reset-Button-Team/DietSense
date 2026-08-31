"""
DietSense — FastAPI Application Entry Point

Phase 1: Scaffold only. Routers for /foods, /recipes, /meal-plans, etc.
will be registered in Phase 4 (Backend API Foundation).

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="DietSense API",
    description=(
        "Evidence-based adaptive meal planning API. "
        "Nutrition facts sourced exclusively from USDA & ICMR-NIN datasets. "
        "LLM (Gemini) is used for natural-language explanations ONLY."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
# Routers will be imported and registered in Phase 4.
# Example (do not uncomment yet):
# from app.routers import auth, foods, recipes, meal_plans, feedback, progress
# app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(foods.router, prefix="/foods", tags=["Foods"])


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check — confirms the API is running."""
    return {
        "status": "ok",
        "service": "DietSense API",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/health", tags=["Health"])
async def detailed_health() -> dict[str, str]:
    """Detailed health check (Phase 4 will add DB connectivity check)."""
    return {
        "status": "ok",
        "api": "healthy",
        "database": "not_connected_yet",  # Phase 3 onwards
        "note": "Phase 1 scaffold — DB connection wired in Phase 3",
    }
