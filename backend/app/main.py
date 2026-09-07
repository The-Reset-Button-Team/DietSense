"""
DietSense — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, foods

app = FastAPI(
    title="DietSense API",
    description=(
        "Evidence-based adaptive meal planning API. "
        "Nutrition facts sourced exclusively from USDA & ICMR-NIN datasets. "
        "LLM (Gemini) is used for natural-language explanations ONLY."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Auth & Profile"])
app.include_router(foods.router, prefix="/api/foods", tags=["Foods Database"])

# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "DietSense API",
        "version": "0.2.0",
        "environment": settings.environment,
    }

@app.get("/health", tags=["Health"])
async def detailed_health() -> dict[str, str]:
    return {
        "status": "ok",
        "api": "healthy",
        "database": "mock_db_ready",
        "auth": "jwt_ready"
    }
