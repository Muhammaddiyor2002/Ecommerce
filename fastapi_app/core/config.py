"""Settings — env-driven via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    env: str = Field("dev", alias="ENV")
    debug: bool = Field(False, alias="DEBUG")
    secret_key: str = Field("dev-secret", alias="SECRET_KEY")

    # Database (FastAPI uses an async SQLAlchemy engine)
    database_url: str = Field(
        "postgresql://novacommerce:novacommerce@localhost:5432/novacommerce",
        alias="DATABASE_URL",
    )
    database_read_url: str = Field("", alias="DATABASE_READ_URL")
    db_pool_size: int = Field(20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(40, alias="DB_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    redis_cache_url: str = Field("redis://localhost:6379/1", alias="REDIS_CACHE_URL")
    redis_channels_url: str = Field("redis://localhost:6379/2", alias="REDIS_CHANNELS_URL")

    # JWT (must match Django SimpleJWT signing key + algorithm)
    jwt_signing_key: str = Field("dev-jwt-key-change", alias="JWT_SIGNING_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    # CORS
    cors_allowed_origins: str = Field("*", alias="CORS_ALLOWED_ORIGINS")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("json", alias="LOG_FORMAT")

    # Sentry
    sentry_dsn: str = Field("", alias="SENTRY_DSN")

    @property
    def async_database_url(self) -> str:
        url = self.database_read_url or self.database_url
        # Convert sync prefix to async per backend.
        if url.startswith("sqlite:"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
            "postgres://", "postgresql+asyncpg://", 1
        )

    @property
    def cors_origins(self) -> list[str]:
        if self.cors_allowed_origins.strip() in {"*", ""}:
            return ["*"]
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
