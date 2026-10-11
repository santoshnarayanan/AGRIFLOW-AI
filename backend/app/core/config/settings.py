"""
Application settings loaded from environment variables via Pydantic BaseSettings.

All secrets are sourced from environment / .env file — never hardcoded.
Azure Key Vault or Docker secrets can inject values as env vars at runtime.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AGRIFLOW-AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ── API ───────────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Database ──────────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agriflow"
    POSTGRES_USER: str = "agriflow"
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password — required")

    DATABASE_URL: str | None = None

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        if self.DATABASE_URL is None:
            self.DATABASE_URL = (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )
        return self

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(..., description="JWT signing secret — required")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # ── Domain events (Phase 14) ──────────────────────────────────────────────
    EVENTS_ENABLED: bool = True
    REDPANDA_ENABLED: bool = False
    REDPANDA_BROKERS: str = "localhost:19092"
    REDPANDA_CLIENT_ID: str = "agriflow-outbox-relay"
    REDPANDA_CONSUMER_GROUP_ID: str = "agriflow-domain-event-audit"
    REDPANDA_BUSINESS_CONSUMER_GROUP_ID: str = "agriflow-business-consumers"
    OUTBOX_RELAY_POLL_INTERVAL_SECONDS: float = 2.0
    OUTBOX_RELAY_BATCH_SIZE: int = 100

    # Business consumers (Phase 14)
    ALERT_EVALUATION_ENABLED: bool = True
    SOIL_MOISTURE_LOW_THRESHOLD_PERCENT: float = 20.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance — safe to call anywhere without re-parsing .env."""
    return Settings()  # type: ignore[call-arg]
