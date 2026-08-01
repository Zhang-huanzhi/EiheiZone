"""Database access helpers for authentication and server-side sessions."""

from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User, UserSession


def get_user_by_login_name(db: Session, login_name: str) -> User | None:
    """Return one user by an already normalized login name."""

    statement = select(User).where(User.login_name == login_name)
    return db.scalar(statement)


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Return one user by its primary key."""

    return db.scalar(select(User).where(User.id == user_id))


def add_user(db: Session, user: User) -> None:
    """Stage a user for the surrounding service transaction."""

    db.add(user)


def add_session(db: Session, login_session: UserSession) -> None:
    """Stage a login session for the surrounding service transaction."""

    db.add(login_session)


def get_session_with_user_by_token_hash(
    db: Session,
    token_hash: str,
) -> UserSession | None:
    """Return a session and its user for one hashed browser credential."""

    statement = (
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.token_hash == token_hash)
    )
    return db.scalar(statement)


def delete_session(db: Session, login_session: UserSession) -> None:
    """Stage deletion of one session without committing it."""

    db.delete(login_session)


def delete_sessions_for_user(db: Session, user_id: UUID) -> int:
    """Stage deletion of every session for a user and return the affected count."""

    result = cast(
        CursorResult[Any],
        db.execute(delete(UserSession).where(UserSession.user_id == user_id)),
    )
    return result.rowcount
