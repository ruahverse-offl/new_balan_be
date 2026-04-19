"""
Application configuration via environment variables (Pydantic Settings).

Supports either ``DATABASE_URL`` (direct asyncpg) or Cloud SQL Connector mode when
``INSTANCE_CONNECTION_NAME`` is set (``DB_USER``, ``DB_PASSWORD``, ``DB_NAME`` required).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_settings: Optional["Settings"] = None


class Settings(BaseSettings):
    """
    Loads settings from environment and optional ``.env`` file.

    Database:
    - **Direct**: set ``DATABASE_URL`` (e.g. ``postgresql+asyncpg://...``). Leave
      ``INSTANCE_CONNECTION_NAME`` unset.
    - **Cloud Run + Cloud SQL**: set ``INSTANCE_CONNECTION_NAME``, ``DB_USER``,
      ``DB_PASSWORD``, ``DB_NAME``. ``DATABASE_URL`` is not required.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = Field(default="change-me-in-production", min_length=1)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: Optional[str] = None
    INSTANCE_CONNECTION_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_METHODS: str = "*"
    CORS_HEADERS: str = "*"

    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "storage/devstorage"
    GCS_BUCKET_NAME: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: Optional[str] = None

    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    INV_STOCK_THRESHOLD: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [x.strip() for x in raw.split(",") if x.strip()]

    @property
    def cors_methods_list(self) -> List[str]:
        raw = (self.CORS_METHODS or "*").strip()
        if raw == "*":
            return ["*"]
        return [x.strip() for x in raw.split(",") if x.strip()]

    @property
    def cors_headers_list(self) -> List[str]:
        raw = (self.CORS_HEADERS or "*").strip()
        if raw == "*":
            return ["*"]
        return [x.strip() for x in raw.split(",") if x.strip()]

    def uses_cloud_sql_connector(self) -> bool:
        """True when connecting via Cloud SQL Python Connector (e.g. Cloud Run)."""
        return bool((self.INSTANCE_CONNECTION_NAME or "").strip())

    def resolved_google_application_credentials_path(self) -> Optional[Path]:
        """
        If ``GOOGLE_APPLICATION_CREDENTIALS`` is set, return the resolved path (absolute if relative).

        The file may or may not exist on disk; callers decide whether to require it.
        Returns ``None`` if unset (typical for Cloud Run: use Application Default Credentials).
        """
        if not self.GOOGLE_APPLICATION_CREDENTIALS or not str(self.GOOGLE_APPLICATION_CREDENTIALS).strip():
            return None
        p = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        return p

    def is_production(self) -> bool:
        return (self.ENVIRONMENT or "").lower() in ("production", "prod")

    @model_validator(mode="after")
    def validate_database_mode(self) -> "Settings":
        if self.uses_cloud_sql_connector():
            missing: List[str] = []
            if not (self.DB_USER or "").strip():
                missing.append("DB_USER")
            if self.DB_PASSWORD is None or str(self.DB_PASSWORD) == "":
                missing.append("DB_PASSWORD")
            if not (self.DB_NAME or "").strip():
                missing.append("DB_NAME")
            if missing:
                raise ValueError(
                    "Cloud SQL mode (INSTANCE_CONNECTION_NAME) requires: " + ", ".join(missing)
                )
        else:
            if not (self.DATABASE_URL or "").strip():
                raise ValueError(
                    "DATABASE_URL is required when INSTANCE_CONNECTION_NAME is not set"
                )
        return self


def get_settings() -> Settings:
    """
    Lazy singleton for settings so import order does not eagerly validate env
    before other modules load (and so tests can set env first).
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
