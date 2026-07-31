from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core import security
from app.core.security import (
    constant_time_equal,
    generate_session_token,
    hash_password,
    hash_session_token,
    issue_csrf_token,
    verify_password,
    verify_csrf_token,
)


TEST_PASSWORD = "test-only-password"
TEST_CSRF_SECRET = "test-csrf-secret-with-at-least-thirty-two-characters"
TOKEN_ISSUED_AT = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def configure_csrf_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        csrf_secret=TEST_CSRF_SECRET,
        csrf_token_ttl_seconds=3600,
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)


def test_password_hash_uses_argon2id_and_a_unique_salt() -> None:
    first_hash = hash_password(TEST_PASSWORD)
    second_hash = hash_password(TEST_PASSWORD)

    assert first_hash.startswith("$argon2id$")
    assert second_hash.startswith("$argon2id$")
    assert first_hash != second_hash
    assert TEST_PASSWORD not in first_hash
    assert TEST_PASSWORD not in second_hash


def test_verify_password_accepts_the_matching_password() -> None:
    password_hash = hash_password(TEST_PASSWORD)

    assert verify_password(TEST_PASSWORD, password_hash) is True


def test_verify_password_rejects_an_incorrect_password() -> None:
    password_hash = hash_password(TEST_PASSWORD)

    assert verify_password("incorrect-test-password", password_hash) is False


def test_verify_password_rejects_an_unknown_hash_format() -> None:
    assert verify_password(TEST_PASSWORD, "not-a-password-hash") is False


def test_generate_session_token_returns_unique_url_safe_values() -> None:
    first_token = generate_session_token()
    second_token = generate_session_token()

    assert first_token != second_token
    assert len(first_token) >= 43
    assert len(second_token) >= 43
    assert first_token.isascii()
    assert second_token.isascii()


def test_hash_session_token_returns_a_stable_sha256_hex_digest() -> None:
    raw_token = "test-session-token"
    token_hash = hash_session_token(raw_token)

    assert token_hash == hash_session_token(raw_token)
    assert len(token_hash) == 64
    assert all(character in "0123456789abcdef" for character in token_hash)
    assert raw_token not in token_hash


def test_different_session_tokens_have_different_hashes() -> None:
    first_token = generate_session_token()
    second_token = generate_session_token()

    assert hash_session_token(first_token) != hash_session_token(second_token)


def test_constant_time_equal_accepts_only_matching_values() -> None:
    assert constant_time_equal("matching-token", "matching-token") is True
    assert constant_time_equal("first-token", "second-token") is False


def test_issue_and_verify_csrf_token_for_the_matching_context() -> None:
    token = issue_csrf_token("anonymous", now=TOKEN_ISSUED_AT)

    assert verify_csrf_token(
        token,
        "anonymous",
        now=TOKEN_ISSUED_AT + timedelta(minutes=30),
    ) is True


def test_verify_csrf_token_rejects_a_tampered_token() -> None:
    token = issue_csrf_token("anonymous", now=TOKEN_ISSUED_AT)
    tampered_token = token.replace(".", "_", 1)

    assert verify_csrf_token(
        tampered_token,
        "anonymous",
        now=TOKEN_ISSUED_AT,
    ) is False


def test_verify_csrf_token_rejects_an_expired_token() -> None:
    token = issue_csrf_token("anonymous", now=TOKEN_ISSUED_AT)

    assert verify_csrf_token(
        token,
        "anonymous",
        now=TOKEN_ISSUED_AT + timedelta(hours=1, seconds=1),
    ) is False


def test_verify_csrf_token_rejects_the_wrong_context() -> None:
    token = issue_csrf_token("session-a", now=TOKEN_ISSUED_AT)

    assert verify_csrf_token(token, "session-b", now=TOKEN_ISSUED_AT) is False


def test_verify_csrf_token_rejects_invalid_structure() -> None:
    assert verify_csrf_token(
        "not-a-csrf-token",
        "anonymous",
        now=TOKEN_ISSUED_AT,
    ) is False


def test_issue_csrf_token_requires_a_configured_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: SimpleNamespace(csrf_secret=None, csrf_token_ttl_seconds=3600),
    )

    with pytest.raises(RuntimeError, match="CSRF_SECRET"):
        issue_csrf_token("anonymous", now=TOKEN_ISSUED_AT)
