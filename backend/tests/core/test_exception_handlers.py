from uuid import UUID

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.errors import AppError, register_exception_handlers
from app.core.pagination import Page, Pagination
from app.core.request_id import request_id_middleware
from app.main import app as main_app


class InputPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)
    register_exception_handlers(app)

    @app.get("/validation")
    def validate_limit(limit: int = Query(ge=1, le=100)) -> dict[str, int]:
        return {"limit": limit}

    @app.get("/conflict")
    def raise_conflict() -> None:
        raise AppError(
            status_code=409,
            code="STATE_CONFLICT",
            message="The resource cannot be changed in its current state",
        )

    @app.get("/unexpected")
    def raise_unexpected_error() -> None:
        raise RuntimeError("database password must not appear in the response")

    @app.post("/input")
    def validate_input(payload: InputPayload) -> dict[str, str]:
        return {"title": payload.title}

    @app.get("/items", response_model=Page[str])
    def list_items(pagination: Pagination) -> Page[str]:
        all_items = [f"item-{index}" for index in range(50)]
        items = all_items[pagination.offset : pagination.offset + pagination.limit]
        return Page(
            items=items,
            total=len(all_items),
            offset=pagination.offset,
            limit=pagination.limit,
        )

    return app


def assert_error_response(response: object, *, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    body = response.json()
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    assert isinstance(body["error"]["field_errors"], list)
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    assert body["error"]["request_id"] == request_id


def test_main_app_formats_a_missing_route_as_a_not_found_error() -> None:
    with TestClient(main_app) as client:
        response = client.get("/api/v1/not-found")

    assert_error_response(response, status_code=404, code="NOT_FOUND")


def test_validation_error_has_a_field_path() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/validation?limit=101")

    assert_error_response(response, status_code=422, code="VALIDATION_ERROR")
    assert response.json()["error"]["field_errors"][0]["field"] == "query.limit"


def test_app_error_uses_its_own_status_and_code() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/conflict")

    assert_error_response(response, status_code=409, code="STATE_CONFLICT")


def test_unexpected_error_does_not_expose_its_detail() -> None:
    with TestClient(create_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    assert_error_response(response, status_code=500, code="INTERNAL_SERVER_ERROR")
    assert "password" not in response.text


def test_valid_request_body_returns_a_normal_response() -> None:
    with TestClient(create_test_app()) as client:
        response = client.post("/input", json={"title": "A valid title"})

    assert response.status_code == 200
    assert response.json() == {"title": "A valid title"}


def test_invalid_request_body_returns_a_unified_field_error() -> None:
    with TestClient(create_test_app()) as client:
        response = client.post("/input", json={"title": ""})

    assert_error_response(response, status_code=422, code="VALIDATION_ERROR")
    assert response.json()["error"]["field_errors"][0]["field"] == "body.title"


def test_pagination_uses_default_offset_and_limit() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == {
        "items": [f"item-{index}" for index in range(20)],
        "total": 50,
        "offset": 0,
        "limit": 20,
    }


def test_pagination_uses_the_requested_offset_and_limit() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/items?offset=20&limit=10")

    assert response.status_code == 200
    assert response.json() == {
        "items": [f"item-{index}" for index in range(20, 30)],
        "total": 50,
        "offset": 20,
        "limit": 10,
    }


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("offset=-1", "query.offset"),
        ("limit=0", "query.limit"),
        ("limit=101", "query.limit"),
        ("limit=not-a-number", "query.limit"),
    ],
)
def test_invalid_pagination_returns_a_unified_field_error(
    query: str,
    field: str,
) -> None:
    with TestClient(create_test_app()) as client:
        response = client.get(f"/items?{query}")

    assert_error_response(response, status_code=422, code="VALIDATION_ERROR")
    assert response.json()["error"]["field_errors"][0]["field"] == field
