from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Validated settings shared by the backend application."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "EiheiZone API"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    app_timezone: str = "Asia/Shanghai"
    database_url: str
    test_database_url: str | None = None
    app_origin: str = "http://localhost:3000"
    csrf_secret: str | None = None
    cookie_secure: bool = False
    session_ttl_days: int = 30
    csrf_token_ttl_seconds: int = 3600

    session_cookie_name: Literal["pfp_session"] = "pfp_session"
    csrf_cookie_name: Literal["pfp_csrf"] = "pfp_csrf"

    @field_validator("app_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            message = "APP_TIMEZONE must be a valid IANA timezone"
            raise ValueError(message) from error
        return value

    @field_validator("app_origin")
    @classmethod
    def validate_app_origin(cls, value: str) -> str:
        parsed = urlsplit(value)
        normalized_origin = f"{parsed.scheme}://{parsed.netloc}"

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or value != normalized_origin
        ):
            message = "APP_ORIGIN must be an origin without a path, query, or fragment"
            raise ValueError(message)
        return value

    @field_validator("csrf_secret")
    @classmethod
    def validate_csrf_secret(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 32:
            message = "CSRF_SECRET must contain at least 32 characters"
            raise ValueError(message)
        return value

    @field_validator("session_ttl_days")
    @classmethod
    def validate_session_ttl_days(cls, value: int) -> int:
        if value != 30:
            message = "SESSION_TTL_DAYS must be 30 because V1 does not use sliding sessions"
            raise ValueError(message)
        return value

    @field_validator("csrf_token_ttl_seconds")
    @classmethod
    def validate_csrf_token_ttl_seconds(cls, value: int) -> int:
        if value <= 0:
            message = "CSRF_TOKEN_TTL_SECONDS must be greater than zero"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env != "production":
            return self

        if self.csrf_secret is None or self.csrf_secret.startswith("replace-with-"):
            message = "A real CSRF_SECRET is required in production"
            raise ValueError(message)
        if not self.cookie_secure:
            message = "COOKIE_SECURE must be true in production"
            raise ValueError(message)
        if not self.app_origin.startswith("https://"):
            message = "APP_ORIGIN must use HTTPS in production"
            raise ValueError(message)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
