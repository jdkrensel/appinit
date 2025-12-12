"""Runtime configuration package.

This package provides centralized configuration management for the application.
Import the settings object to access configuration values throughout your application.

Example:
    >>> from config import settings
    >>> print(settings.app_name)
    >>> print(settings.database_url.get_secret_value())
"""

from config.settings import settings

__all__ = ["settings"]
