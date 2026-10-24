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
        # Inspect token header without verifying to check algorithm
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg", algorithm)

        # Base decode options
        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": bool(settings.jwt_audience),
        }
        decode_kwargs = {
            "algorithms": [token_alg],
            "options": decode_options,
        }
        if settings.jwt_audience:
            decode_kwargs["audience"] = settings.jwt_audience

        # If token is signed with asymmetric algorithm (e.g. ES256 for Supabase ECC P-256 or RS256)
        if token_alg in ["ES256", "RS256"] and settings.supabase_url:
            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            jwks_client = jwt.PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decode_kwargs["key"] = signing_key.key
        else:
            decode_kwargs["key"] = secret
            decode_kwargs["algorithms"] = [algorithm, "HS256"]

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
