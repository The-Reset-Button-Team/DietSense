"""
DietSense — FastAPI Dependency Injections

Extracts and validates verified user credentials from either:
1. HttpOnly session cookies (for browser clients)
2. Bearer tokens in Authorization header (for API / CLI clients)
"""

import jwt
from datetime import datetime, timezone
from typing import Generator, Annotated, Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.security import decode_access_token, normalize_email
from db.database import get_db_cursor, get_connection

security = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Yields a SQLite database connection within a safe transaction context."""
    with get_db_cursor() as cur:
        yield cur


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
) -> Dict[str, Any]:
    """
    Validates user authentication token from either:
    - Authorization: Bearer <token>
    - Cookie: dietsense_session=<token>

    Extracts user identity strictly from the verified JWT 'sub' claim.
    Never trusts client-supplied user IDs. Never logs the raw token.
    Ensures authenticated identity is provisioned in SQLite users table.
    """
    token: Optional[str] = None

    # 1. Check Bearer token from header
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    elif "authorization" in request.headers:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    # 2. Check HttpOnly session cookie
    if not token:
        cookie_name = settings.session_cookie_name
        token = request.cookies.get(cookie_name)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
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

    user_id_str = str(user_id)
    raw_email = payload.get("email") or f"{user_id_str}@dietsense.local"
    email = normalize_email(raw_email)
    full_name = payload.get("user_metadata", {}).get("full_name") or email.split("@")[0]
    now = datetime.now(timezone.utc).isoformat()

    # Ensure user record exists in SQLite to satisfy foreign key integrity
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id_str,))
        if not cur.fetchone():
            # If email is already taken by another user_id, make it unique to avoid constraint collision
            cur.execute("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (email,))
            existing = cur.fetchone()
            effective_email = email if not existing else f"{user_id_str}_{email}"

            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
                VALUES (?, ?, '', ?, 'active', ?, ?)
                """,
                (user_id_str, effective_email, full_name, now, now),
            )

    return {
        "id": user_id_str,
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "app_metadata": payload.get("app_metadata", {}),
        "user_metadata": payload.get("user_metadata", {}),
    }
