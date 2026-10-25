"""
DietSense — Application Configuration

Type-safe, validated configuration for local-first execution.
Defaults to local SQLite database and secure local session handling.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DEFAULT_DB_PATH = os.path.join(_REPO_ROOT, "database", "dietsense.db")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Local Database ────────────────────────────────────────────────────
    sqlite_db_path: str = _DEFAULT_DB_PATH
    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH}"

    # ─── Supabase (Deprecated / Optional compatibility placeholders) ───────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ─── Auth & Security ───────────────────────────────────────────────────
    jwt_secret: str = "dietsense-local-dev-secret-key-32chars-minimum-needed"
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "authenticated"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Cookie settings
    session_cookie_name: str = "dietsense_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"

    # ─── Gemini API (Removed / Deprecated) ─────────────────────────────────
    gemini_api_key: str = ""

    # ─── App ───────────────────────────────────────────────────────────────
    environment: str = "development"
    cors_origins_str: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this via FastAPI Depends."""
    return Settings()


# Module-level singleton for non-DI usage
settings = get_settings()
