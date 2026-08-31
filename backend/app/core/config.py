"""
DietSense — Application Configuration

Reads all environment variables from .env (via python-dotenv).
Using Pydantic Settings for type-safe, validated configuration.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:password@localhost:5432/dietsense"

    # ─── Supabase ──────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # ─── Auth ──────────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # ─── Gemini API ────────────────────────────────────────────────────────
    gemini_api_key: str = ""

    # ─── App ───────────────────────────────────────────────────────────────
    environment: str = "development"
    cors_origins_str: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this via FastAPI Depends."""
    return Settings()


# Module-level singleton for non-DI usage
settings = get_settings()
