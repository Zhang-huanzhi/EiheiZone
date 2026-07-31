import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import session as db_session


class FakeSession:
    def __init__(self) -> None:
        self.rollback_called = False
        self.close_called = False

    def rollback(self) -> None:
        self.rollback_called = True

    def close(self) -> None:
        self.close_called = True


def test_test_database_connection(test_session: Session) -> None:
    database_name, user_name = test_session.execute(
        text("SELECT current_database(), current_user")
    ).one()

    assert database_name == "eiheizone_test"
    assert user_name == "eiheizone_app"


def test_get_db_rolls_back_and_closes_after_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(db_session, "SessionLocal", lambda: fake_session)
    dependency = db_session.get_db()

    assert next(dependency) is fake_session

    with pytest.raises(RuntimeError, match="request failed"):
        dependency.throw(RuntimeError("request failed"))

    assert fake_session.rollback_called is True
    assert fake_session.close_called is True
