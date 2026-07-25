from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "CSRF_SECRET",
    "test-csrf-secret-with-at-least-thirty-two-characters",
)

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app


TEST_DATABASE_NAME = "eiheizone_test"


def get_test_database_url() -> str:
    """Return the configured test URL only when it targets the test database."""

    database_url = get_settings().test_database_url
    if database_url is None:
        raise RuntimeError("TEST_DATABASE_URL is required to run database tests")

    if make_url(database_url).database != TEST_DATABASE_NAME:
        message = f"Database tests must target {TEST_DATABASE_NAME}"
        raise RuntimeError(message)

    return database_url


@pytest.fixture
def test_engine() -> Generator[Engine]:
    engine = create_engine(get_test_database_url(), pool_pre_ping=True)
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
