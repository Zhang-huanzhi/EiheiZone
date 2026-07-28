from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.core.security as security
import app.modules.auth.dependencies as auth_dependencies
import app.modules.auth.router as auth_router
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.qas.models import QA


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_qa_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
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
    login_name = f"qa-api-{label}-{uuid4().hex}"
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


def test_qa_api_has_no_public_read_path_and_requires_authentication(client: TestClient) -> None:
    list_response = client.get("/api/v1/qas")
    public_response = client.get("/api/v1/public/qas")

    assert list_response.status_code == 401
    assert list_response.json()["error"]["code"] == "UNAUTHORIZED"
    assert public_response.status_code == 404


def test_family_question_owner_answer_and_family_wide_read_flow(
    client: TestClient,
    test_session: Session,
) -> None:
    family_a_name = create_account(test_session, UserRole.FAMILY, "Family A")
    family_b_name = create_account(test_session, UserRole.FAMILY, "Family B")
    owner_name = create_account(test_session, UserRole.OWNER, "Owner")

    family_a_csrf = login_with_csrf(client, family_a_name)
    created = client.post(
        "/api/v1/qas",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_a_csrf},
        json={"question": "Can another family member read this?"},
    )
    assert created.status_code == 201
    qa_id = created.json()["id"]
    assert created.json()["status"] == "unanswered"
    assert created.json()["answer"] is None

    owner_csrf = login_with_csrf(client, owner_name)
    owner_cannot_ask = client.post(
        "/api/v1/qas",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"question": "Owner must not ask"},
    )
    answered = client.put(
        f"/api/v1/qas/{qa_id}/answer",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"answer": "Yes, every Family user can read it."},
    )
    replaced = client.put(
        f"/api/v1/qas/{qa_id}/answer",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"answer": "Updated current answer."},
    )

    family_b_csrf = login_with_csrf(client, family_b_name)
    family_list = client.get("/api/v1/qas")
    family_detail = client.get(f"/api/v1/qas/{qa_id}")
    family_cannot_answer = client.put(
        f"/api/v1/qas/{qa_id}/answer",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_b_csrf},
        json={"answer": "Not allowed"},
    )
    qa_count = test_session.scalar(select(func.count()).select_from(QA))

    assert owner_cannot_ask.status_code == 403
    assert answered.status_code == 200
    assert answered.json()["status"] == "answered"
    assert answered.json()["answered_by_display_name"] == "API Owner"
    assert replaced.status_code == 200
    assert replaced.json()["id"] == qa_id
    assert family_list.status_code == 200
    assert family_list.json()["items"][0]["asked_by_display_name"] == "API Family A"
    assert family_detail.json()["answer"] == "Updated current answer."
    assert family_cannot_answer.status_code == 403
    assert qa_count == 1


def test_qa_writes_require_csrf_and_validate_text_fields(
    client: TestClient,
    test_session: Session,
) -> None:
    family_name = create_account(test_session, UserRole.FAMILY, "Validation Family")
    family_csrf = login_with_csrf(client, family_name)

    missing_csrf = client.post(
        "/api/v1/qas",
        headers={"Origin": ORIGIN},
        json={"question": "Missing CSRF"},
    )
    invalid_question = client.post(
        "/api/v1/qas",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_csrf},
        json={"question": "   "},
    )

    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    assert invalid_question.status_code == 422
    assert invalid_question.json()["error"]["field_errors"][0]["field"] == "body.question"


def test_owner_answer_validates_fields_and_missing_resource(
    client: TestClient,
    test_session: Session,
) -> None:
    owner_name = create_account(test_session, UserRole.OWNER, "Validation Owner")
    owner_csrf = login_with_csrf(client, owner_name)

    invalid_answer = client.put(
        f"/api/v1/qas/{uuid4()}/answer",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"answer": "\n\t"},
    )
    missing_qa = client.put(
        f"/api/v1/qas/{uuid4()}/answer",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"answer": "Valid answer"},
    )

    assert invalid_answer.status_code == 422
    assert invalid_answer.json()["error"]["field_errors"][0]["field"] == "body.answer"
    assert missing_qa.status_code == 404
    assert missing_qa.json()["error"]["code"] == "QA_NOT_FOUND"
