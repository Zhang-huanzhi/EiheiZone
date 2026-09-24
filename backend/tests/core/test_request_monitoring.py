import asyncio
import logging
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import Response
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

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
    previous_disabled = logger.disabled
    logger.setLevel(logging.INFO)
    logger.disabled = False
    logger.addHandler(handler)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.disabled = previous_disabled


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
        raise RuntimeError(
            "internal failure: SQL SELECT secret WHERE id=:id "
            "bound_param=family-secret business_data=private"
        )

    @app.get("/db-success")
    def db_success(session: Session = Depends(db_session.get_db)) -> dict[str, int]:
        value = session.execute(text("SELECT 1")).scalar_one()
        return {"value": value}

    @app.get("/db-failure")
    def db_failure(session: Session = Depends(db_session.get_db)) -> None:
        session.execute(text("SELECT 1 / 0"))

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
    for sensitive_value in (
        "internal failure",
        "SELECT secret",
        "bound_param=family-secret",
        "private",
    ):
        assert sensitive_value not in response.text

    error = get_log_record(request_log_records, "Unhandled request error")
    assert error.exc_info is None
    assert error.exc_text is None
    assert error.exception_category == ExceptionCategory.UNHANDLED.value
    for sensitive_value in (
        "internal failure",
        "SELECT secret",
        "bound_param=family-secret",
        "private",
    ):
        assert sensitive_value not in error.getMessage()

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


def test_postgresql_success_query_is_counted_and_timed(test_engine: Engine) -> None:
    metrics = RequestMetrics()
    token = set_request_metrics(metrics)
    try:
        with test_engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        reset_request_metrics(token)

    assert metrics.query_count == 1
    assert metrics.db_duration_ms >= 0
    assert metrics._started_queries == {}


def test_postgresql_failed_query_is_timed_without_open_context(
    test_engine: Engine,
) -> None:
    metrics = RequestMetrics()
    token = set_request_metrics(metrics)
    try:
        with test_engine.connect() as connection:
            with pytest.raises(SQLAlchemyError):
                connection.execute(text("SELECT 1 / 0"))
    finally:
        reset_request_metrics(token)

    assert metrics.query_count == 1
    assert metrics.db_duration_ms >= 0
    assert metrics._started_queries == {}


def test_postgresql_request_metrics_are_isolated_in_slow_logs(
    test_engine: Engine,
    request_log_records: list[logging.LogRecord],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(request_id_module, "get_slow_request_threshold_ms", lambda: 1)
    app = create_monitoring_app()

    def override_get_db():
        connection = test_engine.connect()
        transaction = connection.begin()
        session = sessionmaker(
            bind=connection,
            autoflush=False,
            expire_on_commit=False,
        )()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            if transaction.is_active:
                transaction.rollback()
            connection.close()

    app.dependency_overrides[db_session.get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            success = client.get("/db-success")
            failure = client.get("/db-failure")
    finally:
        app.dependency_overrides.pop(db_session.get_db, None)

    assert success.status_code == 200
    assert failure.status_code == 500
    slow_records = [
        record
        for record in request_log_records
        if record.getMessage() == "Slow request"
    ]
    assert len(slow_records) == 2
    by_request_id = {record.request_id: record for record in slow_records}
    assert by_request_id[success.headers["X-Request-ID"]].db_query_count == 1
    assert by_request_id[failure.headers["X-Request-ID"]].db_query_count == 1
    assert (
        by_request_id[success.headers["X-Request-ID"]].exception_category
        == ExceptionCategory.NONE.value
    )
    assert (
        by_request_id[failure.headers["X-Request-ID"]].exception_category
        == ExceptionCategory.UNHANDLED.value
    )
