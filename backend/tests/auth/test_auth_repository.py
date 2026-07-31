from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserRole, UserSession
from app.modules.auth.repository import (
    add_session,
    add_user,
    delete_session,
    delete_sessions_for_user,
    get_session_with_user_by_token_hash,
    get_user_by_id,
    get_user_by_login_name,
)


def make_user(login_name: str) -> User:
    return User(
        login_name=login_name,
        display_name="Repository Test User",
        role=UserRole.FAMILY,
        password_hash="$argon2id$test-hash",
    )


def make_session(user: User, token_hash: str) -> UserSession:
    return UserSession(
        user=user,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )


def test_user_repository_reads_a_staged_user(test_session: Session) -> None:
    user = make_user("repository-user")
    add_user(test_session, user)
    test_session.flush()

    assert get_user_by_login_name(test_session, "repository-user") == user
    assert get_user_by_id(test_session, user.id) == user
    assert get_user_by_login_name(test_session, "missing-user") is None
    assert get_user_by_id(test_session, UUID(int=0)) is None


def test_session_lookup_returns_its_user(test_session: Session) -> None:
    login_session = make_session(make_user("repository-session"), "a" * 64)
    add_session(test_session, login_session)
    test_session.flush()
    test_session.expunge_all()

    found_session = get_session_with_user_by_token_hash(test_session, "a" * 64)

    assert found_session is not None
    assert found_session.user.login_name == "repository-session"
    assert get_session_with_user_by_token_hash(test_session, "b" * 64) is None


def test_delete_session_stages_only_the_requested_session(test_session: Session) -> None:
    first_session = make_session(make_user("repository-first"), "c" * 64)
    second_session = make_session(make_user("repository-second"), "d" * 64)
    test_session.add_all([first_session, second_session])
    test_session.flush()

    delete_session(test_session, first_session)
    test_session.flush()

    assert get_session_with_user_by_token_hash(test_session, "c" * 64) is None
    assert get_session_with_user_by_token_hash(test_session, "d" * 64) is not None


def test_delete_sessions_for_user_returns_affected_count(test_session: Session) -> None:
    user = make_user("repository-delete-all")
    test_session.add_all(
        [
            make_session(user, "e" * 64),
            make_session(user, "f" * 64),
        ]
    )
    test_session.flush()

    deleted_count = delete_sessions_for_user(test_session, user.id)
    test_session.flush()

    assert deleted_count == 2
    assert get_session_with_user_by_token_hash(test_session, "e" * 64) is None
    assert get_session_with_user_by_token_hash(test_session, "f" * 64) is None
