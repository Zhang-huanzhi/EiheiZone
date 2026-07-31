from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.core.security as security
import app.modules.auth.dependencies as auth_dependencies
import app.modules.auth.router as auth_router
from app.core.security import hash_session_token
from app.modules.auth.models import AccountStatus, UserRole
from app.modules.auth.repository import get_session_with_user_by_token_hash
from app.modules.auth.service import create_user, login, reset_password


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        app_origin=ORIGIN,
        csrf_secret="test-csrf-secret-with-at-least-thirty-two-characters",
        csrf_token_ttl_seconds=3600,
        session_cookie_name="pfp_session",
        csrf_cookie_name="pfp_csrf",
        cookie_secure=False,
        session_ttl_days=30,
    )
    def get_test_settings() -> SimpleNamespace:
        return settings

    monkeypatch.setattr(security, "get_settings", get_test_settings)
    monkeypatch.setattr(auth_dependencies, "get_settings", get_test_settings)
    monkeypatch.setattr(auth_router, "get_settings", get_test_settings)


def create_account(test_session: Session, role: UserRole) -> str:
    login_name = f"{role.value}-{uuid4().hex}"
    create_user(
        test_session,
        login_name=login_name,
        display_name=f"{role.value.title()} User",
        role=role,
        plain_password=PASSWORD,
    )
    return login_name


def login_with_csrf(client: TestClient, login_name: str):
    csrf_response = client.get("/api/v1/auth/csrf")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.json()["csrf_token"]

    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response


def test_login_me_logout_and_bound_csrf_token(client: TestClient, test_session: Session) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)

    login_response = login_with_csrf(client, login_name)
    assert login_response.json()["user"]["login_name"] == login_name
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert "Max-Age=2592000" in login_response.headers["set-cookie"]
    assert "Path=/" in login_response.headers["set-cookie"]
    assert "SameSite=lax" in login_response.headers["set-cookie"]

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "family"

    csrf_response = client.get("/api/v1/auth/csrf")
    assert csrf_response.status_code == 200
    rotated_csrf_token = csrf_response.json()["csrf_token"]
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": rotated_csrf_token},
    )
    assert logout_response.status_code == 204
    assert "Max-Age=0" in logout_response.headers["set-cookie"]
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rejects_missing_or_invalid_csrf_and_wrong_password(
    client: TestClient,
    test_session: Session,
) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)

    missing_csrf = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"

    csrf_response = client.get("/api/v1/auth/csrf")
    wrong_origin = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000.attacker.example", "X-CSRF-Token": csrf_response.json()["csrf_token"]},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert wrong_origin.status_code == 403

    invalid_password = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_response.json()["csrf_token"]},
        json={"login_name": login_name, "password": "wrong-password"},
    )
    assert invalid_password.status_code == 401
    assert invalid_password.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_mismatched_csrf_without_creating_a_session(
    client: TestClient,
    test_session: Session,
) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)
    csrf_response = client.get("/api/v1/auth/csrf")

    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": f"other-{csrf_response.json()['csrf_token']}"},
        json={"login_name": login_name, "password": PASSWORD},
    )

    assert response.status_code == 403
    assert client.cookies.get("pfp_session") is None


def test_expired_session_cannot_access_me(client: TestClient, test_session: Session) -> None:
    login_name = create_account(test_session, UserRole.OWNER)
    login_with_csrf(client, login_name)
    raw_token = client.cookies.get("pfp_session")
    login_session = get_session_with_user_by_token_hash(
        test_session,
        hash_session_token(raw_token),
    )
    assert login_session is not None
    login_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    test_session.flush()

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_inactive_user_and_random_token_cannot_access_me(client: TestClient, test_session: Session) -> None:
    login_name = create_account(test_session, UserRole.OWNER)
    login_with_csrf(client, login_name)
    raw_token = client.cookies.get("pfp_session")
    login_session = get_session_with_user_by_token_hash(test_session, hash_session_token(raw_token))
    assert login_session is not None
    login_session.user.status = AccountStatus.INACTIVE
    test_session.flush()

    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set("pfp_session", "not-a-real-session-token")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_only_invalidates_its_current_session(client: TestClient, test_session: Session) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)
    first = login(test_session, login_name=login_name, plain_password=PASSWORD)
    second = login(test_session, login_name=login_name, plain_password=PASSWORD)
    csrf_token = security.issue_csrf_token(str(first.session.id))
    client.cookies.set("pfp_session", first.raw_token)
    client.cookies.set("pfp_csrf", csrf_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 204
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(first.raw_token)) is None
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(second.raw_token)) is not None


def test_session_csrf_token_cannot_authorize_another_session(
    client: TestClient,
    test_session: Session,
) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)
    first = login(test_session, login_name=login_name, plain_password=PASSWORD)
    second = login(test_session, login_name=login_name, plain_password=PASSWORD)
    second_csrf_token = security.issue_csrf_token(str(second.session.id))
    client.cookies.set("pfp_session", first.raw_token)
    client.cookies.set("pfp_csrf", second_csrf_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": second_csrf_token},
    )

    assert response.status_code == 403
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(first.raw_token)) is not None
    assert get_session_with_user_by_token_hash(test_session, hash_session_token(second.raw_token)) is not None


def test_reset_password_invalidates_old_cookie_and_old_password(
    client: TestClient,
    test_session: Session,
) -> None:
    login_name = create_account(test_session, UserRole.FAMILY)
    login_with_csrf(client, login_name)
    reset_password(test_session, login_name=login_name, plain_password="new-password-456")

    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.clear()
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    old_password = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert old_password.status_code == 401

    new_password = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": "new-password-456"},
    )
    assert new_password.status_code == 200


def test_family_cannot_satisfy_owner_dependency(test_session: Session) -> None:
    from app.modules.auth.dependencies import CurrentUser, get_current_user, require_family_access, require_owner
    from app.core.errors import AppError

    user = create_user(
        test_session,
        login_name=f"family-{uuid4().hex}",
        display_name="Family User",
        role=UserRole.FAMILY,
        plain_password=PASSWORD,
    )

    try:
        require_owner(CurrentUser(user=user, session_id="session-id"))
    except AppError as error:
        assert error.status_code == 403
        assert error.code == "FORBIDDEN"
    else:
        raise AssertionError("Family users must not satisfy the Owner dependency")

    assert require_family_access(CurrentUser(user=user, session_id="session-id")) is not None
    with pytest.raises(AppError, match="Authentication is required"):
        get_current_user(test_session, None)


def test_owner_satisfies_both_role_dependencies(test_session: Session) -> None:
    from app.modules.auth.dependencies import CurrentUser, require_family_access, require_owner

    user = create_user(
        test_session,
        login_name=f"owner-{uuid4().hex}",
        display_name="Owner User",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )
    current_user = CurrentUser(user=user, session_id="session-id")

    assert require_family_access(current_user) == current_user
    assert require_owner(current_user) == current_user
