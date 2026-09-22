import asyncio
import logging
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI, Query, Request
from fastapi.responses import Response
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import request_id as request_id_module
from app.core.errors import AppError, register_exception_handlers
from app.core.request_metrics import (
    ExceptionCategory,
    RequestMetrics,
    get_request_metrics,
    reset_request_metrics,
    set_request_metrics,
)
from app.db import session as db_session


class ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def request_log_records() -> list[logging.LogRecord]:
    handler = ListHandler()
    logger = request_id_module.logger
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


def create_monitoring_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(request_id_module.request_id_middleware)
    register_exception_handlers(app)

    @app.get("/ok")
    def ok() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/slow")
    def slow() -> Response:
        return Response(status_code=201)

    @app.get("/http-error")
    def http_error() -> None:
        raise StarletteHTTPException(status_code=403)

    @app.get("/app-error")
    def app_error() -> None:
        raise AppError(
            status_code=409,
            code="STATE_CONFLICT",
            message="The resource cannot be changed in its current state",
        )

    @app.get("/validation")
    def validation(limit: int = Query(ge=1)) -> dict[str, int]:
        return {"limit": limit}

    @app.get("/unhandled")
    def unhandled() -> None:
        raise RuntimeError("internal failure")

    return app


def set_clock(monkeypatch: pytest.MonkeyPatch, *values: float) -> None:
    clock_values = iter(values)
    monkeypatch.setattr(
        request_id_module,
        "perf_counter",
        lambda: next(clock_values),
    )


def get_log_record(
    records: list[logging.LogRecord], message: str
) -> logging.LogRecord:
    records = [record for record in records if record.getMessage() == message]
    assert len(records) == 1
    return records[0]


def test_request_below_threshold_does_not_emit_slow_log(
    monkeypatch: pytest.MonkeyPatch,
    request_log_records: list[logging.LogRecord],
) -> None:
    set_clock(monkeypatch, 0.0, 0.299)
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 300)

    with TestClient(create_monitoring_app()) as client:
        response = client.get("/ok")

    assert response.status_code == 200
    assert not [
        record
        for record in request_log_records
        if record.getMessage() == "Slow request"
    ]
    completed = get_log_record(request_log_records, "Request completed")
    assert completed.duration_ms == 299.0
    assert completed.exception_category == ExceptionCategory.NONE.value


def test_slow_log_contains_request_and_database_fields(
    monkeypatch: pytest.MonkeyPatch,
    request_log_records: list[logging.LogRecord],
) -> None:
    set_clock(monkeypatch, 0.0, 0.301)
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 300)

    with TestClient(create_monitoring_app()) as client:
        response = client.post("/slow")

    assert response.status_code == 201
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    slow = get_log_record(request_log_records, "Slow request")
    assert slow.request_id == request_id
    assert slow.method == "POST"
    assert slow.path == "/slow"
    assert slow.status_code == 201
    assert slow.duration_ms == 301.0
    assert slow.exception_category == ExceptionCategory.NONE.value
    assert slow.db_query_count == 0
    assert slow.db_duration_ms == 0.0


@pytest.mark.parametrize(
    ("path", "expected_status", "expected_category"),
    [
        ("/http-error", 403, ExceptionCategory.HTTP),
        ("/app-error", 409, ExceptionCategory.APP),
        ("/validation?limit=0", 422, ExceptionCategory.VALIDATION),
    ],
)
def test_handled_errors_are_classified_in_request_log(
    path: str,
    expected_status: int,
    expected_category: ExceptionCategory,
    monkeypatch: pytest.MonkeyPatch,
    request_log_records: list[logging.LogRecord],
) -> None:
    set_clock(monkeypatch, 0.0, 0.001)
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 300)

    with TestClient(create_monitoring_app()) as client:
        response = client.get(path)

    assert response.status_code == expected_status
    completed = get_log_record(request_log_records, "Request completed")
    assert completed.status_code == expected_status
    assert completed.exception_category == expected_category.value


def test_unhandled_error_is_classified_without_exposing_details(
    monkeypatch: pytest.MonkeyPatch,
    request_log_records: list[logging.LogRecord],
) -> None:
    set_clock(monkeypatch, 0.0, 0.301)
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 300)

    with TestClient(create_monitoring_app(), raise_server_exceptions=False) as client:
        response = client.get("/unhandled")

    assert response.status_code == 500
    assert "internal failure" not in response.text
    slow = get_log_record(request_log_records, "Slow request")
    assert slow.status_code == 500
    assert slow.exception_category == ExceptionCategory.UNHANDLED.value


def test_cancelled_request_is_logged_with_status_499(
    monkeypatch: pytest.MonkeyPatch,
    request_log_records: list[logging.LogRecord],
) -> None:
    set_clock(monkeypatch, 0.0, 0.301)
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 300)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/cancelled",
            "headers": [],
            "query_string": b"",
        }
    )

    async def call_next(_: Request) -> Response:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(request_id_module.request_id_middleware(request, call_next))

    slow = get_log_record(request_log_records, "Slow request")
    assert slow.status_code == 499
    assert slow.exception_category == ExceptionCategory.CANCELLED.value


def test_database_query_metrics_aggregate_and_reset() -> None:
    metrics = RequestMetrics()
    token = set_request_metrics(metrics)
    first_context = object()
    second_context = object()
    try:
        metrics.start_query(first_context)
        metrics.start_query(second_context)
        assert metrics.query_count == 2
    finally:
        reset_request_metrics(token)

    assert get_request_metrics() is None


def test_database_event_callbacks_count_queries_without_sql_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = RequestMetrics()
    token = set_request_metrics(metrics)
    execution_context = object()
    clock_values = iter([1.0, 1.125])
    monkeypatch.setattr(
        "app.core.request_metrics.perf_counter",
        lambda: next(clock_values),
    )
    try:
        db_session._before_cursor_execute(
            object(), object(), "SELECT secret", (), execution_context, False
        )
        db_session._after_cursor_execute(
            object(), object(), "SELECT secret", (), execution_context, False
        )
    finally:
        reset_request_metrics(token)

    assert metrics.query_count == 1
    assert metrics.db_duration_ms == 125.0


def test_database_error_callback_finishes_query(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics = RequestMetrics()
    token = set_request_metrics(metrics)
    execution_context = object()
    clock_values = iter([1.0, 1.125])
    monkeypatch.setattr(
        "app.core.request_metrics.perf_counter",
        lambda: next(clock_values),
    )
    try:
        db_session._before_cursor_execute(
            object(), object(), "SELECT secret", (), execution_context, False
        )
        db_session._handle_error(SimpleNamespace(execution_context=execution_context))
    finally:
        reset_request_metrics(token)

    assert metrics.query_count == 1
    assert metrics.db_duration_ms == 125.0
