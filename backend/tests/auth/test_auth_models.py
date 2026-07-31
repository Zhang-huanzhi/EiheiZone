from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountStatus, User, UserRole, UserSession


def create_user(login_name: str) -> User:
    return User(
        login_name=login_name,
        display_name="Test User",
        role=UserRole.FAMILY,
        password_hash="$argon2id$test-hash",
    )


def test_user_defaults_and_session_relationship_persist(test_session: Session) -> None:
    user = create_user("family-model-test")
    login_session = UserSession(
        user=user,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    test_session.add(login_session)
    test_session.flush()

    assert user.id is not None
    assert user.status is AccountStatus.ACTIVE
    assert user.created_at.tzinfo is not None
    assert user.updated_at.tzinfo is not None
    assert login_session.user_id == user.id
    assert login_session.user == user


def test_deleting_a_user_cascades_to_its_sessions(test_session: Session) -> None:
    user = create_user("family-cascade-test")
    login_session = UserSession(
        user=user,
        token_hash="b" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    test_session.add(login_session)
    test_session.flush()

    session_id = login_session.id
    test_session.delete(user)
    test_session.flush()
    test_session.expire_all()

    assert test_session.get(UserSession, session_id) is None


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("role", "public"),
        ("status", "disabled"),
    ],
)
def test_user_database_constraints_reject_invalid_role_or_status(
    test_session: Session,
    column: str,
    value: str,
) -> None:
    values = {
        "id": uuid4(),
        "login_name": f"invalid-{column}-{uuid4()}",
        "display_name": "Invalid User",
        "role": UserRole.FAMILY.value,
        "status": AccountStatus.ACTIVE.value,
        "password_hash": "$argon2id$test-hash",
    }
    values[column] = value

    with pytest.raises(IntegrityError):
        test_session.execute(
            text(
                """
                INSERT INTO users (id, login_name, display_name, role, password_hash, status)
                VALUES (:id, :login_name, :display_name, :role, :password_hash, :status)
                """
            ),
            values,
        )

    test_session.rollback()


def test_session_token_hash_is_unique(test_session: Session) -> None:
    first_user = create_user("family-token-one")
    second_user = create_user("family-token-two")
    token_hash = "c" * 64
    test_session.add_all(
        [
            UserSession(
                user=first_user,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            ),
            UserSession(
                user=second_user,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        test_session.flush()

    test_session.rollback()


def test_session_requires_an_existing_user(test_session: Session) -> None:
    test_session.add(
        UserSession(
            user_id=uuid4(),
            token_hash="d" * 64,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )

    with pytest.raises(IntegrityError):
        test_session.flush()

    test_session.rollback()
