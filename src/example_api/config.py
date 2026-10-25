"""Settings, read from ``EXAMPLE_API_*`` environment variables or a ``.env`` file."""

from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthMode(StrEnum):
    """How requests to protected routes are authenticated."""

    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"


class Settings(BaseSettings):
    """Application settings. List values are given as JSON, for example ``["a", "b"]``."""

    model_config = SettingsConfigDict(env_prefix="EXAMPLE_API_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    workers: int = Field(default=1, ge=1)
    shutdown_timeout: int = Field(
        default=10, ge=1, description="Seconds to finish requests on shutdown."
    )
    docs_enabled: bool = True
    rate_limit_per_minute: int = Field(
        default=120, ge=0, description="Requests per client per minute; 0 turns the limit off."
    )
    max_body_bytes: int = Field(default=1_048_576, ge=1)
    cors_origins: list[str] = []
    allowed_hosts: list[str] = []
    root_path: str = ""
    forwarded_allow_ips: str = "127.0.0.1"

    auth_mode: AuthMode = AuthMode.NONE
    api_keys: list[SecretStr] = []
    jwt_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_audience: str | None = None
    jwt_issuer: str | None = None

    @model_validator(mode="after")
    def _check_auth_settings(self) -> Self:
        """Fail at startup, not on the first request, if authentication is misconfigured."""
        if self.auth_mode is AuthMode.API_KEY and not self.api_keys:
            raise ValueError("EXAMPLE_API_API_KEYS is required when auth_mode is api_key")
        if self.auth_mode is AuthMode.JWT and self.jwt_key is None:
            raise ValueError("EXAMPLE_API_JWT_KEY is required when auth_mode is jwt")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read once per process."""
    return Settings()
