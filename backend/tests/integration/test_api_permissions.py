from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.core.security as security
import app.modules.auth.dependencies as auth_dependencies
import app.modules.auth.router as auth_router
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_permission_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
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
    login_name = f"permission-{role.value}-{uuid4().hex}"
    create_user(
        test_session,
        login_name=login_name,
        display_name=f"Permission {role.value.title()}",
        role=role,
        plain_password=PASSWORD,
    )
    return login_name


def login_with_csrf(client: TestClient, login_name: str) -> str:
    client.cookies.clear()
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/v1/auth/me", None),
        ("post", "/api/v1/auth/logout", None),
        ("get", "/api/v1/posts", None),
        ("get", f"/api/v1/posts/{uuid4()}", None),
        ("post", "/api/v1/posts", {"title": "Post", "body": "Body"}),
        ("patch", f"/api/v1/posts/{uuid4()}", {"title": "Updated"}),
        ("delete", f"/api/v1/posts/{uuid4()}", None),
        ("get", "/api/v1/qas", None),
        ("get", f"/api/v1/qas/{uuid4()}", None),
        ("post", "/api/v1/qas", {"question": "Question"}),
        ("put", f"/api/v1/qas/{uuid4()}/answer", {"answer": "Answer"}),
        ("get", "/api/v1/expenditures", None),
        ("get", f"/api/v1/expenditures/{uuid4()}", None),
        (
            "post",
            "/api/v1/expenditures",
            {
                "spent_on": "2026-07-30",
                "amount": "100.0000",
                "currency": "CNY",
                "category": "Test",
                "description": "Synthetic test expenditure",
            },
        ),
        ("patch", f"/api/v1/expenditures/{uuid4()}", {"category": "Updated"}),
        ("delete", f"/api/v1/expenditures/{uuid4()}", None),
        ("get", "/api/v1/dashboard", None),
    ],
)
def test_public_is_rejected_by_every_protected_operation(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = client.request(method, path, json=payload)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/api/v1/posts", {"title": "Post", "body": "Body"}),
        ("patch", f"/api/v1/posts/{uuid4()}", {"title": "Updated"}),
        ("delete", f"/api/v1/posts/{uuid4()}", None),
        ("put", f"/api/v1/qas/{uuid4()}/answer", {"answer": "Answer"}),
        (
            "post",
            "/api/v1/expenditures",
            {
                "spent_on": "2026-07-30",
                "amount": "100.0000",
                "currency": "CNY",
                "category": "Test",
                "description": "Synthetic test expenditure",
            },
        ),
        ("patch", f"/api/v1/expenditures/{uuid4()}", {"category": "Updated"}),
        ("delete", f"/api/v1/expenditures/{uuid4()}", None),
    ],
)
def test_family_is_rejected_by_every_owner_write_operation_with_valid_csrf(
    client: TestClient,
    test_session: Session,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    csrf_token = login_with_csrf(
        client,
        create_account(test_session, UserRole.FAMILY),
    )

    response = client.request(
        method,
        path,
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json=payload,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_owner_cannot_submit_a_family_question_with_valid_csrf(
    client: TestClient,
    test_session: Session,
) -> None:
    csrf_token = login_with_csrf(
        client,
        create_account(test_session, UserRole.OWNER),
    )

    response = client.post(
        "/api/v1/qas",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"question": "Owner must not submit a Family question"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
