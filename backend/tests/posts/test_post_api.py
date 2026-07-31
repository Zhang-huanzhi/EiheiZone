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
from app.modules.posts.service import create_post
from app.modules.posts.schemas import PostCreate


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_post_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
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
    login_name = f"post-api-{role.value}-{uuid4().hex}"
    create_user(
        test_session,
        login_name=login_name,
        display_name=f"{role.value.title()} API User",
        role=role,
        plain_password=PASSWORD,
    )
    return login_name


def login_with_csrf(client: TestClient, login_name: str) -> str:
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_public_api_never_returns_family_only_posts(client: TestClient, test_session: Session) -> None:
    owner = create_user(
        test_session,
        login_name=f"post-api-owner-{uuid4().hex}",
        display_name="API Owner",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )
    public_post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Public update", body="Public body", visibility="public"),
    )
    family_post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Family update", body="Family body"),
    )

    list_response = client.get("/api/v1/public/posts")
    family_detail = client.get(f"/api/v1/public/posts/{family_post.id}")
    public_detail = client.get(f"/api/v1/public/posts/{public_post.id}")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [str(public_post.id)]
    assert family_detail.status_code == 404
    assert family_detail.json()["error"]["code"] == "POST_NOT_FOUND"
    assert public_detail.status_code == 200


def test_authenticated_readers_and_owner_write_permissions(client: TestClient, test_session: Session) -> None:
    owner_name = create_account(test_session, UserRole.OWNER)
    family_name = create_account(test_session, UserRole.FAMILY)

    owner_csrf = login_with_csrf(client, owner_name)
    created = client.post(
        "/api/v1/posts",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={"title": "Family only", "body": "Family content"},
    )
    assert created.status_code == 201
    post_id = created.json()["id"]

    client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": client.get("/api/v1/auth/csrf").json()["csrf_token"]},
    )
    family_csrf = login_with_csrf(client, family_name)
    readable = client.get("/api/v1/posts")
    forbidden = client.patch(
        f"/api/v1/posts/{post_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": family_csrf},
        json={"title": "Not allowed"},
    )

    assert readable.status_code == 200
    assert readable.json()["items"][0]["id"] == post_id
    assert forbidden.status_code == 403


def test_owner_post_writes_require_bound_csrf_and_validate_fields(
    client: TestClient,
    test_session: Session,
) -> None:
    owner_name = create_account(test_session, UserRole.OWNER)
    csrf_token = login_with_csrf(client, owner_name)

    missing_csrf = client.post(
        "/api/v1/posts",
        headers={"Origin": ORIGIN},
        json={"title": "Missing CSRF", "body": "Body"},
    )
    invalid_fields = client.post(
        "/api/v1/posts",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"title": " ", "body": "Body"},
    )
    created = client.post(
        "/api/v1/posts",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"title": "Original", "body": "Original body"},
    )
    post_id = created.json()["id"]
    empty_patch = client.patch(
        f"/api/v1/posts/{post_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={},
    )
    deleted = client.delete(
        f"/api/v1/posts/{post_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
    )

    assert missing_csrf.status_code == 403
    assert invalid_fields.status_code == 422
    assert created.status_code == 201
    assert empty_patch.status_code == 422
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/posts/{post_id}").status_code == 404
