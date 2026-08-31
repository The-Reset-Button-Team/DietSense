"""
DietSense — FastAPI Dependency Injections

Phase 1: Scaffold only.
Phase 3 will implement get_db() with real Supabase/SQLAlchemy session.
Phase 4 will implement get_current_user() with JWT validation.
"""

from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ─── Security scheme ─────────────────────────────────────────────────────────
security = HTTPBearer()


# ─── Database Session ─────────────────────────────────────────────────────────
def get_db() -> Generator:
    """
    Yields a SQLAlchemy database session.
    Phase 3 implementation: create engine from settings.database_url,
    yield session, close on exit.

    Usage:
        @router.get("/example")
        async def example(db: Session = Depends(get_db)):
            ...
    """
    # TODO (Phase 3): Replace with real session factory
    # from app.db.session import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    raise NotImplementedError("Database session not wired yet — implement in Phase 3.")


# ─── Current User ─────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """
    Validates the Supabase JWT from the Authorization header.
    Phase 4 implementation: decode JWT, fetch user from DB, return user object.

    Usage:
        @router.get("/me")
        async def me(user: dict = Depends(get_current_user)):
            ...
    """
    # TODO (Phase 4): Replace with real JWT verification
    # from jose import jwt, JWTError
    # from app.core.config import settings
    # try:
    #     payload = jwt.decode(credentials.credentials, settings.jwt_secret, ...)
    #     user_id = payload.get("sub")
    #     ...
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not implemented yet — wire in Phase 4.",
    )
