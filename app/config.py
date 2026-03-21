"""
Application Configuration Module

This module provides centralized configuration management using Pydantic Settings.
All configuration values are read from environment variables with sensible defaults.
"""

import os
from typing import Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, field_serializer


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class uses Pydantic Settings to automatically load configuration
    from environment variables, .env files, and provide type validation.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="None"
    )
    
    # ==================== Application Settings ====================
    APP_NAME: str = Field(default="NEW Balan", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_DESCRIPTION: str = Field(
        default="Backend API for NEW Balan",
        description="Application description"
    )
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development, dev, qa, staging, production, prod)"
    )
    
    # ==================== Server Settings ====================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    # ==================== Database Settings ====================
    DATABASE_URL: str | None = Field(
        default=None,
        description="Full PostgreSQL connection URL"
    )
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(default="postgres", description="Database password")
    DB_NAME: str = Field(default="NEW_Balan", description="Database name")
    DB_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DB_MAX_OVERFLOW: int = Field(
        default=20,
        description="Maximum overflow connections"
    )
    
    # ==================== JWT Authentication Settings ====================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm (HS256, RS256, etc.)"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # ==================== Storage Backend Settings ====================
    STORAGE_BACKEND: Literal["local", "azure"] = Field(
        default="local",
        description="Storage backend (local or azure)"
    )
    
    # Local Storage Settings
    LOCAL_STORAGE_PATH: str = Field(
        default="./storage",
        description="Local file storage path"
    )
    
    # Azure Blob Storage Settings
    AZURE_STORAGE_ACCOUNT_NAME: str | None = Field(
        default=None,
        description="Azure Storage Account name"
    )
    AZURE_STORAGE_ACCOUNT_KEY: str | None = Field(
        default=None,
        description="Azure Storage Account key"
    )
    AZURE_STORAGE_CONTAINER_NAME: str | None = Field(
        default=None,
        description="Azure Storage Container name"
    )
    AZURE_STORAGE_CONNECTION_STRING: str | None = Field(
        default=None,
        description="Azure Storage Connection String"
    )
    
    # ==================== CORS Settings ====================
    # These fields are stored as strings in .env and converted to lists by validators
    CORS_ORIGINS: str = Field(
        default="*",
        description="Allowed CORS origins (comma-separated string, e.g., 'http://localhost:3000,http://localhost:3001' or '*' for all)"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    CORS_ALLOW_METHODS: str = Field(
        default="*",
        description="Allowed HTTP methods (comma-separated string, e.g., 'GET,POST,PUT,DELETE' or '*' for all)"
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="*",
        description="Allowed HTTP headers (comma-separated string, e.g., 'Content-Type,Authorization' or '*' for all)"
    )
    
    # ==================== Logging Settings ====================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # ==================== Razorpay Payment Gateway Settings ====================
    RAZORPAY_KEY_ID: str = Field(
        default="",
        description="Razorpay Key ID (public key for frontend checkout)"
    )
    RAZORPAY_KEY_SECRET: str = Field(
        default="",
        description="Razorpay Key Secret (for server-side API calls)"
    )
    RAZORPAY_WEBHOOK_SECRET: str = Field(
        default="",
        description="Optional: Razorpay webhook secret for server-to-server verification"
    )

    # ==================== Pagination Settings ====================
    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        description="Default pagination page size"
    )
    MAX_PAGE_SIZE: int = Field(
        default=100,
        description="Maximum pagination page size"
    )
    
    # ==================== Request/Response Settings ====================
    REQUEST_TIMEOUT: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=10485760,  # 10MB in bytes
        description="Maximum upload file size in bytes"
    )

    # ==================== Inventory / low-stock alerts ====================
    INV_STOCK_THRESHOLD: int = Field(
        default=10,
        ge=0,
        description="When on-hand stock for a medicine+brand (offering) falls below this count, an inventory alert is raised; refills at or above this level remove the alert.",
    )
    
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "dev", "qa", "staging", "production", "prod"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        # Normalize to standard names
        env_map = {
            "dev": "development",
            "prod": "production"
        }
        return env_map.get(v_lower, v_lower)
    
    def get_database_url(self) -> str:
        """
        Get the complete database connection URL.
        
        Returns:
            str: PostgreSQL connection URL
            
        If DATABASE_URL is set, it will be used. Otherwise, the URL will be
        constructed from individual database components.
        """
        if self.DATABASE_URL:
            # Ensure the URL uses asyncpg driver
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            elif not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                return f"postgresql+asyncpg://{self.DATABASE_URL}"
            return self.DATABASE_URL
        
        # Build from components
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list (converted from string)."""
        origins = self.CORS_ORIGINS
        if not origins or origins.strip() == "" or origins.strip() == "*":
            return ["*"]
        # Handle comma-separated values
        result = [o.strip() for o in origins.split(",") if o.strip()]
        return result if result else ["*"]
    
    @property
    def cors_methods_list(self) -> list[str]:
        """Get CORS methods as a list (converted from string)."""
        methods = self.CORS_ALLOW_METHODS
        if not methods or methods.strip() == "" or methods.strip() == "*":
            return ["*"]
        # Handle comma-separated values
        result = [m.strip() for m in methods.split(",") if m.strip()]
        return result if result else ["*"]
    
    @property
    def cors_headers_list(self) -> list[str]:
        """Get CORS headers as a list (converted from string)."""
        headers = self.CORS_ALLOW_HEADERS
        if not headers or headers.strip() == "" or headers.strip() == "*":
            return ["*"]
        # Handle comma-separated values
        result = [h.strip() for h in headers.split(",") if h.strip()]
        return result if result else ["*"]


# Create a singleton instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the application settings instance.
    
    This function provides dependency injection support for FastAPI.
    
    Returns:
        Settings: Application settings instance
        
    Example usage in FastAPI route:
        @app.get("/config")
        async def get_config(settings: Settings = Depends(get_settings)):
            return {"environment": settings.ENVIRONMENT}
    """
    return settings
