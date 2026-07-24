from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_session_token, verify_password
from app.modules.auth.models import UserRole
from app.modules.auth.repository import get_session_with_user_by_token_hash
from app.modules.auth.service import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, create_user, login, logout, reset_password


PASSWORD = "test-password-123"


def unique_login_name(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def test_create_user_normalizes_names_and_hashes_password(test_session: Session) -> None:
    login_name = unique_login_name("family-a")
    user = create_user(
        test_session,
        login_name=f" {login_name.upper()} ",
        display_name=" Family A ",
        role=UserRole.FAMILY,
        plain_password=PASSWORD,
    )

    assert user.login_name == login_name
    assert user.display_name == "Family A"
    assert verify_password(PASSWORD, user.password_hash)


@pytest.mark.parametrize("password", ["x" * (MIN_PASSWORD_LENGTH - 1), "x" * (MAX_PASSWORD_LENGTH + 1)])
def test_create_user_rejects_passwords_outside_the_shared_length_rule(
    test_session: Session,
    password: str,
) -> None:
    with pytest.raises(AppError, match="Password is invalid"):
        create_user(
            test_session,
            login_name=unique_login_name("invalid-password"),
            display_name="Invalid Password",
            role=UserRole.FAMILY,
            plain_password=password,
        )


def test_login_creates_a_fixed_expiry_session(test_session: Session) -> None:
    login_name = unique_login_name("owner")
    create_user(test_session, login_name=login_name, display_name="Owner", role=UserRole.OWNER, plain_password=PASSWORD)
    issued_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    authenticated = login(test_session, login_name=login_name.upper(), plain_password=PASSWORD, now=issued_at)

    assert authenticated.session.expires_at == issued_at + timedelta(days=30)
    assert authenticated.raw_token != authenticated.session.token_hash
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(authenticated.raw_token)) is not None


def test_login_uses_one_error_for_missing_user_and_bad_password(test_session: Session) -> None:
    login_name = unique_login_name("family")
    create_user(test_session, login_name=login_name, display_name="Family", role=UserRole.FAMILY, plain_password=PASSWORD)

    with pytest.raises(AppError, match="login name or password") as missing:
        login(test_session, login_name="missing", plain_password=PASSWORD)
    with pytest.raises(AppError, match="login name or password") as wrong_password:
        login(test_session, login_name=login_name, plain_password="wrong-password")

    assert missing.value.code == wrong_password.value.code == "INVALID_CREDENTIALS"


def test_reset_password_invalidates_all_existing_sessions(test_session: Session) -> None:
    login_name = unique_login_name("reset-user")
    create_user(test_session, login_name=login_name, display_name="Reset User", role=UserRole.FAMILY, plain_password=PASSWORD)
    first = login(test_session, login_name=login_name, plain_password=PASSWORD)
    second = login(test_session, login_name=login_name, plain_password=PASSWORD)

    user, deleted_count = reset_password(test_session, login_name=login_name, plain_password="new-password-456")

    assert deleted_count == 2
    assert verify_password("new-password-456", user.password_hash)
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(first.raw_token)) is None
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(second.raw_token)) is None


@pytest.mark.parametrize("operation", ["create", "login", "reset", "logout"])
def test_write_services_roll_back_when_commit_fails(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    login_name = unique_login_name(f"rollback-{operation}")
    create_user(
        test_session,
        login_name=login_name,
        display_name="Rollback User",
        role=UserRole.FAMILY,
        plain_password=PASSWORD,
    )
    authenticated = login(test_session, login_name=login_name, plain_password=PASSWORD)
    rollback_calls = 0
    original_rollback = test_session.rollback

    def fail_commit() -> None:
        raise OperationalError("COMMIT", {}, None)

    def record_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback()

    monkeypatch.setattr(test_session, "commit", fail_commit)
    monkeypatch.setattr(test_session, "rollback", record_rollback)

    with pytest.raises(OperationalError):
        if operation == "create":
            create_user(
                test_session,
                login_name=unique_login_name("failed-create"),
                display_name="Failed Create",
                role=UserRole.FAMILY,
                plain_password=PASSWORD,
            )
        elif operation == "login":
            login(test_session, login_name=login_name, plain_password=PASSWORD)
        elif operation == "reset":
            reset_password(test_session, login_name=login_name, plain_password="new-password-456")
        else:
            logout(test_session, raw_token=authenticated.raw_token)

    assert rollback_calls == 1
