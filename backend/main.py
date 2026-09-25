"""
DietSense - FastAPI Application Entrypoint
Initializes the FastAPI app, registers CORS middleware, routes, and /health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.users import router as users_router
from routes.foods import router as foods_router
from routes.recommendations import router as recommendations_router
from routes.feedback import router as feedback_router

app = FastAPI(
    title="DietSense API",
    description="Adaptive AI Meal Planning System Backend",
    version="1.0.0",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(users_router)
app.include_router(foods_router)
app.include_router(recommendations_router)
app.include_router(feedback_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check route returning API status.
    """
    return {"status": "ok", "service": "DietSense FastAPI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
