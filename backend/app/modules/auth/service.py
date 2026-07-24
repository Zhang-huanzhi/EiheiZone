"""Authentication business rules and transaction boundaries."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.modules.auth.models import AccountStatus, User, UserRole, UserSession
from app.modules.auth.repository import (
    add_session,
    add_user,
    delete_session,
    delete_sessions_for_user,
    get_session_with_user_by_token_hash,
    get_user_by_login_name,
)


MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 100


@dataclass(frozen=True)
class AuthenticatedSession:
    """Return the browser-only token separately from its database hash."""

    user: User
    session: UserSession
    raw_token: str


def normalize_login_name(login_name: str) -> str:
    """Return the canonical account identifier used for lookup and uniqueness."""

    return login_name.strip().lower()


def create_user(
    db: Session,
    *,
    login_name: str,
    display_name: str,
    role: UserRole,
    plain_password: str,
) -> User:
    """Create one active Family or Owner account in a committed transaction."""

    normalized_login_name = normalize_login_name(login_name)
    normalized_display_name = display_name.strip()
    _validate_account_input(normalized_login_name, normalized_display_name, plain_password)

    if get_user_by_login_name(db, normalized_login_name) is not None:
        raise AppError(
            status_code=409,
            code="LOGIN_NAME_CONFLICT",
            message="The login name is already in use",
        )

    user = User(
        login_name=normalized_login_name,
        display_name=normalized_display_name,
        role=role,
        password_hash=hash_password(plain_password),
    )
    add_user(db, user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AppError(
            status_code=409,
            code="LOGIN_NAME_CONFLICT",
            message="The login name is already in use",
        ) from error
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def login(
    db: Session,
    *,
    login_name: str,
    plain_password: str,
    now: datetime | None = None,
) -> AuthenticatedSession:
    """Verify credentials and create a non-sliding server-side session."""

    user = get_user_by_login_name(db, normalize_login_name(login_name))
    if user is None or user.status is not AccountStatus.ACTIVE:
        raise _invalid_credentials_error()
    if not verify_password(plain_password, user.password_hash):
        raise _invalid_credentials_error()

    issued_at = now or datetime.now(UTC)
    raw_token = generate_session_token()
    login_session = UserSession(
        user=user,
        token_hash=hash_session_token(raw_token),
        expires_at=issued_at + timedelta(days=get_settings().session_ttl_days),
    )
    add_session(db, login_session)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(login_session)
    return AuthenticatedSession(user=user, session=login_session, raw_token=raw_token)


def reset_password(
    db: Session,
    *,
    login_name: str,
    plain_password: str,
) -> tuple[User, int]:
    """Change a password and invalidate every existing session atomically."""

    _validate_password(plain_password)
    user = get_user_by_login_name(db, normalize_login_name(login_name))
    if user is None:
        raise AppError(status_code=404, code="USER_NOT_FOUND", message="User was not found")

    user.password_hash = hash_password(plain_password)
    deleted_count = delete_sessions_for_user(db, user.id)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(user)
    return user, deleted_count


def logout(db: Session, *, raw_token: str) -> None:
    """Invalidate the current server-side session in one transaction."""

    login_session = get_session_with_user_by_token_hash(
        db,
        hash_session_token(raw_token),
    )
    if login_session is None:
        return

    delete_session(db, login_session)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def _validate_account_input(login_name: str, display_name: str, password: str) -> None:
    if not 1 <= len(login_name) <= 100:
        raise AppError(status_code=422, code="INVALID_LOGIN_NAME", message="Login name is invalid")
    if not 1 <= len(display_name) <= 80:
        raise AppError(status_code=422, code="INVALID_DISPLAY_NAME", message="Display name is invalid")
    _validate_password(password)


def _validate_password(password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise AppError(status_code=422, code="INVALID_PASSWORD", message="Password is invalid")


def _invalid_credentials_error() -> AppError:
    return AppError(
        status_code=401,
        code="INVALID_CREDENTIALS",
        message="The login name or password is incorrect",
    )
