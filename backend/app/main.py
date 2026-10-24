"""
DietSense — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, foods
from routes.users import router as users_router
from routes.feedback import router as feedback_router
from routes.recommendations import router as recommendations_router
from routes.foods import router as catalog_foods_router

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
# allow_origins=["*"] combined with allow_credentials=True violates the CORS spec
# (browsers reject it). Use the explicit origins list from config instead.
_cors_origins = settings.cors_origins if settings.cors_origins else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Auth & Profile"])
app.include_router(foods.router, prefix="/api/foods", tags=["Foods Database"])
app.include_router(catalog_foods_router)
app.include_router(users_router)
app.include_router(feedback_router)
app.include_router(recommendations_router)

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
