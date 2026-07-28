"""FastAPI dependencies for authenticated users and CSRF-protected requests."""

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Cookie, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import constant_time_equal, hash_session_token, verify_csrf_token
from app.db.session import get_db
from app.modules.auth.models import AccountStatus, User, UserRole
from app.modules.auth.repository import get_session_with_user_by_token_hash


@dataclass(frozen=True)
class CurrentUser:
    user: User
    session_id: str


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="pfp_session"),
) -> CurrentUser:
    current_user = get_current_user_optional(db, session_token)
    if current_user is None:
        raise _unauthorized()
    return current_user


def get_current_user_optional(
    db: Session,
    session_token: str | None,
) -> CurrentUser | None:
    """Resolve a valid login session without turning anonymous access into an error."""

    if session_token is None:
        return None
    login_session = get_session_with_user_by_token_hash(
        db,
        hash_session_token(session_token),
    )
    if (
        login_session is None
        or login_session.expires_at <= datetime.now(UTC)
        or login_session.user.status is not AccountStatus.ACTIVE
    ):
        return None
    return CurrentUser(user=login_session.user, session_id=str(login_session.id))


def require_family_access(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


def require_family(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.user.role is not UserRole.FAMILY:
        raise AppError(status_code=403, code="FORBIDDEN", message="Family access is required")
    return current_user


def require_owner(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.user.role is not UserRole.OWNER:
        raise AppError(status_code=403, code="FORBIDDEN", message="Owner access is required")
    return current_user


def validate_csrf_request(request: Request, expected_context: str) -> None:
    settings = get_settings()
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    header_token = request.headers.get("X-CSRF-Token")
    if (
        request.headers.get("Origin") != settings.app_origin
        or cookie_token is None
        or header_token is None
        or not constant_time_equal(cookie_token, header_token)
        or not verify_csrf_token(cookie_token, expected_context)
    ):
        raise AppError(status_code=403, code="CSRF_VALIDATION_FAILED", message="Request validation failed")


def _unauthorized() -> AppError:
    return AppError(status_code=401, code="UNAUTHORIZED", message="Authentication is required")
