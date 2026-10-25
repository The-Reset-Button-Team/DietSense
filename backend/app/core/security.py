"""
DietSense — Security & Password Hashing Module
Implements secure password hashing with bcrypt, input normalization,
and JWT generation/verification.
"""

import time
import bcrypt
import jwt
from typing import Optional, Dict, Any
from app.core.config import settings


def normalize_email(email: str) -> str:
    """Consistently normalizes email addresses by trimming and lowercasing."""
    if not email:
        return ""
    return email.strip().lower()


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with automatic salt generation.
    Never stores plaintext passwords.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Securely verifies a plaintext password against a bcrypt hash.
    Safe against timing attacks.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    user_id: str,
    email: str,
    full_name: str = "",
    role: str = "authenticated",
    expires_in_secs: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a signed JWT with user claims.
    Compatible with existing authorization headers and session cookies.
    """
    now = int(time.time())
    exp_secs = expires_in_secs if expires_in_secs is not None else (settings.jwt_expire_minutes * 60)
    payload = {
        "sub": str(user_id),
        "email": normalize_email(email),
        "aud": settings.jwt_audience or "authenticated",
        "role": role,
        "iat": now,
        "exp": now + exp_secs,
        "user_metadata": {
            "full_name": full_name or email.split("@")[0],
        },
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token.
    Enforces signature, expiration, and audience.
    """
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": bool(settings.jwt_audience),
    }
    kwargs: Dict[str, Any] = {
        "algorithms": [settings.jwt_algorithm, "HS256"],
        "options": options,
    }
    if settings.jwt_audience:
        kwargs["audience"] = settings.jwt_audience

    return jwt.decode(token, settings.jwt_secret, **kwargs)
