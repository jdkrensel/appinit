"""Application runtime configuration module.

This module provides runtime configuration management by loading values from
environment variables and optional .env files during application startup.

Configuration Priority (highest to lowest):
    1. Environment variables (production, staging, etc.)
    2. .env file (local development only - gitignored)
    3. Field default values

Installation:
    uv add pydantic-settings

Example:
    >>> from config import settings
    >>> print(settings.app_name)
    >>> print(settings.database_url.get_secret_value())


Note:
    Never commit .env files to version control. Add them to .gitignore.
    Configuration is loaded once at import time and frozen thereafter.
"""

from typing import ClassVar, Final

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with automatic loading from environment variables and .env files."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    # Add your configuration fields here as class attributes:
    #   Required: required_field: str
    #   Optional: optional_field: str = "default_value"
    #   Secret: secret_field: SecretStr
    #
    # Use Field() for advanced configuration like validation, documentation, or aliases:
    #   port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    #   database_url: SecretStr = Field(..., description="PostgreSQL connection string")
    #   api_key: str = Field(alias="API_KEY", description="External API key")


settings: Final[Settings] = Settings()
