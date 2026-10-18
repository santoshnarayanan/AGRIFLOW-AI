"""
Application settings loaded from environment variables via Pydantic BaseSettings.

All secrets are sourced from environment / .env file — never hardcoded.
Azure Key Vault or Docker secrets can inject values as env vars at runtime.
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        In development, ``backend/.env`` wins over process/OS env vars so a
        stale global ``POSTGRES_PORT`` does not override Podman host port 25432.
        Production/staging keep the usual env-var precedence (12-factor).
        """
        if os.getenv("APP_ENV", "development").lower() == "development":
            return (
                init_settings,
                dotenv_settings,
                env_settings,
                file_secret_settings,
            )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
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
    ML_ENGINE_AUTO_RUN_ENABLED: bool = False

    # Outbox operations API (optional; required in staging/production)
    EVENTS_OPS_API_KEY: str | None = Field(
        default=None,
        description="Shared secret for X-Events-Ops-Key on outbox ops and replay routes",
    )

    # ── Feature Store (Phase 15) ───────────────────────────────────────────────
    FEATURE_STORE_REGISTRY_VERSION: str = "cdd-v1.0.0"
    FEATURE_STORE_GDD_BASE_C: float = 10.0

    # ── CQRS read models (Phase 15) ─────────────────────────────────────────────
    READ_MODEL_PROJECTION_VERSION: str = "v1"
    READ_MODEL_AUTO_REFRESH_ON_READ: bool = True

    # ── Digital Twin (Phase 15) ────────────────────────────────────────────────
    DIGITAL_TWIN_STATE_VERSION: str = "twin-v1"
    DIGITAL_TWIN_AUTO_SYNC_ON_READ: bool = True

    # ── Intelligence projections (Phase 15 slice 4) ────────────────────────────
    INTELLIGENCE_EVENT_PROJECTION_ENABLED: bool = True

    # ── Platform auth / RBAC (Phase 15 slice 5) ──────────────────────────────────
    AUTH_REQUIRED: bool = False

    # ── Temporal workflows (Phase 16) ───────────────────────────────────────────
    TEMPORAL_ENABLED: bool = False
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "agriflow-alerts"
    TEMPORAL_SOIL_MOISTURE_PERSISTENCE_MINUTES: int = 15

    # ── Farm Copilot / GaaS (Phase 16) ────────────────────────────────────────────
    COPILOT_ENABLED: bool = True
    COPILOT_AUTH_REQUIRED: bool = False
    COPILOT_LLM_PROVIDER: Literal["none", "openai", "azure"] = "none"
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    # ── MCP tool evaluation (Phase 16) ───────────────────────────────────────────
    MCP_TOOLS_ENABLED: bool = True

    # ── Observability (Phase 16) ─────────────────────────────────────────────────
    METRICS_ENABLED: bool = True

    # ── Security (Phase 16 hardening) ────────────────────────────────────────────
    SECURITY_HEADERS_ENABLED: bool = True

    @model_validator(mode="after")
    def apply_copilot_openai_default(self) -> "Settings":
        """Use OpenAI when a key is configured and provider was left at ``none``."""
        if (
            self.COPILOT_ENABLED
            and self.COPILOT_LLM_PROVIDER == "none"
            and self.OPENAI_API_KEY
            and self.OPENAI_API_KEY.strip()
        ):
            self.COPILOT_LLM_PROVIDER = "openai"
        if self.COPILOT_AUTH_REQUIRED and not self.AUTH_REQUIRED:
            self.AUTH_REQUIRED = True
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance — safe to call anywhere without re-parsing .env."""
    return Settings()  # type: ignore[call-arg]
