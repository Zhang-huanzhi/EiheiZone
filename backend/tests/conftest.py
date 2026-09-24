from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "CSRF_SECRET",
    "test-csrf-secret-with-at-least-thirty-two-characters",
)

from app.core.config import get_settings
from app.db.session import get_db, register_query_monitoring
from app.main import app


TEST_DATABASE_NAME = "eiheizone_test"


def get_test_database_url() -> str:
    """Return the configured test URL only when it targets the test database."""

    database_url = get_settings().test_database_url
    if database_url is None:
        pytest.skip("环境阻塞：TEST_DATABASE_URL 未配置")

    try:
        database_name = make_url(database_url).database
    except ValueError:
        pytest.skip("环境阻塞：TEST_DATABASE_URL 不是有效数据库 URL")

    if database_name != TEST_DATABASE_NAME:
        message = f"Database tests must target {TEST_DATABASE_NAME}"
        pytest.skip(f"环境阻塞：{message}")

    return database_url


@pytest.fixture
def test_engine() -> Generator[Engine]:
    engine = create_engine(get_test_database_url(), pool_pre_ping=True)
    register_query_monitoring(engine)
    try:
        with engine.connect():
            pass
    except SQLAlchemyError as error:
        engine.dispose()
        pytest.skip(
            "环境阻塞：专用 PostgreSQL 测试数据库不可用 "
            f"({type(error).__name__})"
        )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_session(test_engine: Engine) -> Generator[Session]:
    connection: Connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(test_session: Session) -> Generator[TestClient]:
    """Provide the main API app with its database dependency bound to the test Session."""

    def override_get_db() -> Generator[Session]:
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
