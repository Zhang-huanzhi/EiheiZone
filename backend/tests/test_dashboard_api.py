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
from app.modules.expenditures.schemas import ExpenditureCreate
from app.modules.expenditures.service import create_expenditure
from app.modules.posts.schemas import PostCreate
from app.modules.posts.service import create_post
from app.modules.qas.schemas import QACreate
from app.modules.qas.service import create_question


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_dashboard_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
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


def create_account(test_session: Session, role: UserRole, label: str):
    return create_user(
        test_session,
        login_name=f"dashboard-api-{label}-{uuid4().hex}",
        display_name=f"Dashboard API {label}",
        role=role,
        plain_password=PASSWORD,
    )


def login(client: TestClient, login_name: str) -> None:
    client.cookies.clear()
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert response.status_code == 200


def test_dashboard_has_no_public_path_and_requires_authentication(client: TestClient) -> None:
    dashboard = client.get("/api/v1/dashboard")
    public_dashboard = client.get("/api/v1/public/dashboard")

    assert dashboard.status_code == 401
    assert dashboard.json()["error"]["code"] == "UNAUTHORIZED"
    assert public_dashboard.status_code == 404


def test_family_and_owner_receive_the_same_safe_dashboard_contract(
    client: TestClient,
    test_session: Session,
) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Family")
    owner = create_account(test_session, UserRole.OWNER, "Owner")
    post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Dashboard post", body="Dashboard body"),
    )
    qa = create_question(
        test_session,
        user=family,
        payload=QACreate(question="Dashboard pending question"),
    )
    expenditure = create_expenditure(
        test_session,
        user=owner,
        payload=ExpenditureCreate(
            spent_on="2026-07-29",
            amount="1234.5600",
            currency="CNY",
            category="Test category",
            description="Test dashboard expenditure",
        ),
    )

    login(client, family.login_name)
    family_response = client.get("/api/v1/dashboard")
    login(client, owner.login_name)
    owner_response = client.get("/api/v1/dashboard")

    assert family_response.status_code == 200
    assert owner_response.status_code == 200
    for response in (family_response, owner_response):
        body = response.json()
        assert set(body) == {"posts", "qas", "expenditures", "unanswered_qas"}
        assert body["posts"]["items"][0]["id"] == str(post.id)
        assert body["posts"]["total"] == 1
        assert body["qas"]["items"][0]["id"] == str(qa.id)
        assert body["unanswered_qas"]["items"][0]["id"] == str(qa.id)
        assert body["unanswered_qas"]["total"] == 1
        assert body["expenditures"]["items"][0]["id"] == str(expenditure.id)
        assert body["expenditures"]["items"][0]["amount"] == "1234.5600"
        assert isinstance(body["expenditures"]["items"][0]["amount"], str)
        assert "password_hash" not in response.text
        assert "/family/" not in response.text
        assert "/owner/" not in response.text
