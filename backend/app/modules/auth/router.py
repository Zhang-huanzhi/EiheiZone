"""HTTP endpoints for authentication and server-side sessions."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import issue_csrf_token
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_current_user_optional,
    validate_csrf_request,
)
from app.modules.auth.schemas import CsrfResponse, CurrentUserResponse, LoginRequest, LoginResponse
from app.modules.auth.service import login, logout as logout_session


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CsrfResponse)
def get_csrf(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> CsrfResponse:
    settings = get_settings()
    current_user = get_current_user_optional(
        db,
        request.cookies.get(settings.session_cookie_name),
    )
    context = current_user.session_id if current_user is not None else "anonymous"
    token = issue_csrf_token(context)
    _set_csrf_cookie(response, token)
    return CsrfResponse(csrf_token=token)


@router.post("/login", response_model=LoginResponse)
def login_user(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    validate_csrf_request(request, "anonymous")
    authenticated = login(db, login_name=payload.login_name, plain_password=payload.password)
    _set_session_cookie(response, authenticated.raw_token)
    csrf_token = issue_csrf_token(str(authenticated.session.id))
    _set_csrf_cookie(response, csrf_token)
    return LoginResponse(user=CurrentUserResponse.model_validate(authenticated.user), csrf_token=csrf_token)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user.user)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    settings = get_settings()
    logout_session(db, raw_token=request.cookies[settings.session_cookie_name])
    _clear_auth_cookies(response)


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _set_csrf_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        max_age=settings.csrf_token_ttl_seconds,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, secure=settings.cookie_secure, samesite="lax", path="/")
    response.delete_cookie(settings.csrf_cookie_name, secure=settings.cookie_secure, samesite="lax", path="/")
