"""
DietSense — FastAPI Dependency Injections

Phase 1: Scaffold only.
Phase 3 will implement get_db() with real Supabase/SQLAlchemy session.
Phase 4 will implement get_current_user() with JWT validation.
"""

import jwt
from typing import Generator, Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# ─── Security scheme ─────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


# ─── Database Session ─────────────────────────────────────────────────────────
def get_db() -> Generator:
    """
    Yields a SQLAlchemy database session.
    """
    raise NotImplementedError("Database session not wired yet.")


# ─── Current User ─────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> dict:
    """
    Validates the Supabase JWT from the Authorization header.
    Verifies signature, expiry, and audience ('authenticated').
    Extracts the user ID exclusively from the verified token ('sub').
    Never logs or leaks the raw token.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    secret = settings.jwt_secret
    algorithm = settings.jwt_algorithm or "HS256"

    try:
        # Decode and verify Supabase JWT
        decode_kwargs = {
            "key": secret,
            "algorithms": [algorithm],
            "options": {
                "verify_signature": True,
                "verify_exp": True,
            },
        }
        if settings.jwt_audience:
            decode_kwargs["audience"] = settings.jwt_audience
            decode_kwargs["options"]["verify_aud"] = True
        else:
            decode_kwargs["options"]["verify_aud"] = False

        payload = jwt.decode(token, **decode_kwargs)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject (user ID) is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": str(user_id),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "app_metadata": payload.get("app_metadata", {}),
        "user_metadata": payload.get("user_metadata", {}),
    }
