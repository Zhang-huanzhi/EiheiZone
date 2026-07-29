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
BASE_INPUT = {
    "spent_on": "2026-07-28",
    "amount": "1234.5600",
    "currency": "cny",
    "category": "Equipment",
    "description": "Test equipment purchase",
}


@pytest.fixture(autouse=True)
def configure_expenditure_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
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


def create_account(test_session: Session, role: UserRole, label: str) -> str:
    login_name = f"expenditure-api-{label}-{uuid4().hex}"
    create_user(
        test_session,
        login_name=login_name,
        display_name=f"API {label}",
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


def test_expenditure_has_no_public_path_and_requires_authentication(client: TestClient) -> None:
    list_response = client.get("/api/v1/expenditures")
    public_response = client.get("/api/v1/public/expenditures")

    assert list_response.status_code == 401
    assert public_response.status_code == 404


def test_owner_crud_and_family_read_permissions(client: TestClient, test_session: Session) -> None:
    owner_name = create_account(test_session, UserRole.OWNER, "Owner")
    family_name = create_account(test_session, UserRole.FAMILY, "Family")
    owner_csrf = login_with_csrf(client, owner_name)

    created = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json=BASE_INPUT,
    )
    assert created.status_code == 201
    expenditure_id = created.json()["id"]
    assert created.json()["amount"] == "1234.5600"
    assert isinstance(created.json()["amount"], str)
    assert created.json()["currency"] == "CNY"

    updated = client.patch(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"category": "Updated category"},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "1234.5600"

    family_csrf = login_with_csrf(client, family_name)
    family_list = client.get("/api/v1/expenditures")
    family_detail = client.get(f"/api/v1/expenditures/{expenditure_id}")
    forbidden_update = client.patch(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_csrf},
        json={"category": "Forbidden"},
    )
    forbidden_delete = client.delete(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_csrf},
    )

    assert family_list.status_code == 200
    assert family_detail.status_code == 200
    assert family_detail.json()["spent_on"] == "2026-07-28"
    assert forbidden_update.status_code == 403
    assert forbidden_delete.status_code == 403

    owner_csrf = login_with_csrf(client, owner_name)
    deleted = client.delete(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/expenditures/{expenditure_id}").status_code == 404


def test_expenditure_writes_require_csrf_and_reject_invalid_or_private_fields(
    client: TestClient,
    test_session: Session,
) -> None:
    owner_name = create_account(test_session, UserRole.OWNER, "Validation Owner")
    owner_csrf = login_with_csrf(client, owner_name)

    missing_csrf = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN},
        json=BASE_INPUT,
    )
    number_amount = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={**BASE_INPUT, "amount": 1234.56},
    )
    private_field = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={**BASE_INPUT, "card_number": "not-stored"},
    )
    invalid_currency = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={**BASE_INPUT, "currency": "ZZZ"},
    )

    assert missing_csrf.status_code == 403
    assert number_amount.status_code == 422
    assert private_field.status_code == 422
    assert invalid_currency.status_code == 422


def test_expenditure_patch_rejects_empty_null_and_extra_fields(
    client: TestClient,
    test_session: Session,
) -> None:
    owner_name = create_account(test_session, UserRole.OWNER, "Patch Owner")
    owner_csrf = login_with_csrf(client, owner_name)
    created = client.post(
        "/api/v1/expenditures",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json=BASE_INPUT,
    )
    expenditure_id = created.json()["id"]

    empty = client.patch(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={},
    )
    null_amount = client.patch(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"amount": None},
    )
    extra = client.patch(
        f"/api/v1/expenditures/{expenditure_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"receipt": "not-stored"},
    )

    assert empty.status_code == 422
    assert null_amount.status_code == 422
    assert extra.status_code == 422
