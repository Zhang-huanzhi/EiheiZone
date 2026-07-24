"""Shared security primitives used by authentication services."""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

from app.core.config import get_settings


_password_hasher = PasswordHash.recommended()
_SESSION_TOKEN_BYTES = 32
_CSRF_TOKEN_VERSION = "v1"
_CSRF_NONCE_BYTES = 32


def hash_password(plain_password: str) -> str:
    """Return an Argon2id hash without retaining the supplied password."""

    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return whether a password matches a stored hash without exposing parse errors."""

    try:
        return _password_hasher.verify(plain_password, password_hash)
    except PwdlibError:
        return False


def generate_session_token() -> str:
    """Return a URL-safe token with at least 256 bits of randomness."""

    return secrets.token_urlsafe(_SESSION_TOKEN_BYTES)


def hash_session_token(raw_token: str) -> str:
    """Return the fixed-length database representation of a session token."""

    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def constant_time_equal(first_value: str, second_value: str) -> bool:
    """Compare untrusted token values without leaking where they differ."""

    return hmac.compare_digest(
        first_value.encode("utf-8"),
        second_value.encode("utf-8"),
    )


def issue_csrf_token(context: str, *, now: datetime | None = None) -> str:
    """Issue a signed, short-lived CSRF token bound to one security context."""

    if not context:
        raise ValueError("CSRF token context must not be empty")

    issued_at = _as_utc_timestamp(now)
    nonce = secrets.token_urlsafe(_CSRF_NONCE_BYTES)
    encoded_context = _encode_token_component(context)
    payload = ".".join(
        (_CSRF_TOKEN_VERSION, str(issued_at), nonce, encoded_context)
    )
    signature = hmac.new(
        _get_csrf_secret().encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def verify_csrf_token(
    token: str,
    expected_context: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a token has a valid signature, age, and bound context."""

    if not expected_context:
        return False

    try:
        version, issued_at_text, nonce, encoded_context, signature = token.split(".")
        issued_at = int(issued_at_text)
    except (AttributeError, ValueError):
        return False

    if (
        version != _CSRF_TOKEN_VERSION
        or not nonce
        or encoded_context != _encode_token_component(expected_context)
    ):
        return False

    payload = ".".join((version, issued_at_text, nonce, encoded_context))
    expected_signature = hmac.new(
        _get_csrf_secret().encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not constant_time_equal(signature, expected_signature):
        return False

    current_timestamp = _as_utc_timestamp(now)
    token_age = current_timestamp - issued_at
    return 0 <= token_age <= get_settings().csrf_token_ttl_seconds


def _get_csrf_secret() -> str:
    secret = get_settings().csrf_secret
    if secret is None:
        raise RuntimeError("CSRF_SECRET must be configured before issuing CSRF tokens")
    return secret


def _encode_token_component(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _as_utc_timestamp(now: datetime | None) -> int:
    if now is None:
        return int(datetime.now(UTC).timestamp())
    if now.tzinfo is None:
        raise ValueError("CSRF token time must include a timezone")
    return int(now.astimezone(UTC).timestamp())
