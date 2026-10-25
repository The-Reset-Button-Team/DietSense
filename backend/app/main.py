"""
DietSense — FastAPI Application Entry Point
Local-first adaptive meal planning API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, foods
from routes.users import router as users_router
from routes.feedback import router as feedback_router
from routes.recommendations import router as recommendations_router
from routes.foods import router as catalog_foods_router
from routes.meal_plans import router as meal_plans_router
from routes.meal_logs import router as meal_logs_router
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes local SQLite database tables on application startup."""
    init_db()
    yield


app = FastAPI(
    title="DietSense API",
    description=(
        "Local-first evidence-based adaptive meal planning API. "
        "Nutrition facts sourced exclusively from USDA & ICMR-NIN datasets."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
_cors_origins = settings.cors_origins if settings.cors_origins else ["http://localhost:3000", "http://127.0.0.1:3000"]
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
app.include_router(meal_plans_router)
app.include_router(meal_logs_router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "DietSense API",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health", tags=["Health"])
async def detailed_health() -> dict[str, str]:
    return {
        "status": "ok",
        "api": "healthy",
        "database": "sqlite_ready",
        "auth": "local_jwt_session_ready",
    }
