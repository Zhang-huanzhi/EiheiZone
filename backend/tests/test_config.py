import pytest
from pydantic import ValidationError

from app.core.config import Settings


DATABASE_URL = "postgresql+psycopg://user:password@127.0.0.1:5432/eiheizone_dev"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": DATABASE_URL,
        "test_database_url": DATABASE_URL.replace("eiheizone_dev", "eiheizone_test"),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_development_auth_defaults_are_local_safe() -> None:
    settings = make_settings()

    assert settings.app_origin == "http://localhost:3000"
    assert settings.cookie_secure is False
    assert settings.session_ttl_days == 30
    assert settings.session_cookie_name == "pfp_session"
    assert settings.csrf_cookie_name == "pfp_csrf"


@pytest.mark.parametrize(
    "origin",
    [
        "localhost:3000",
        "http://localhost:3000/",
        "http://localhost:3000/login",
        "http://localhost:3000?next=/login",
        "http://user:password@localhost:3000",
    ],
)
def test_app_origin_must_be_a_plain_origin(origin: str) -> None:
    with pytest.raises(ValidationError, match="APP_ORIGIN"):
        make_settings(app_origin=origin)


@pytest.mark.parametrize(
    "overrides",
    [
        {"app_env": "production"},
        {
            "app_env": "production",
            "csrf_secret": "a" * 32,
            "cookie_secure": True,
        },
        {
            "app_env": "production",
            "csrf_secret": "a" * 32,
            "app_origin": "https://portal.example.test",
        },
        {
            "app_env": "production",
            "app_origin": "https://portal.example.test",
            "csrf_secret": "replace-with-a-long-random-secret-before-production",
            "cookie_secure": True,
        },
    ],
)
def test_production_requires_complete_cookie_and_csrf_configuration(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        make_settings(**overrides)


def test_production_accepts_secure_cookie_https_origin_and_csrf_secret() -> None:
    settings = make_settings(
        app_env="production",
        app_origin="https://portal.example.test",
        csrf_secret="a" * 32,
        cookie_secure=True,
    )

    assert settings.app_env == "production"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("csrf_secret", "short-secret"),
        ("session_ttl_days", 29),
        ("csrf_token_ttl_seconds", 0),
    ],
)
def test_auth_security_settings_reject_invalid_values(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: value})
