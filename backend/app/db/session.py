from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.request_metrics import get_request_metrics

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


def _before_cursor_execute(
    connection: object,
    cursor: object,
    statement: str,
    parameters: object,
    execution_context: object,
    executemany: bool,
) -> None:
    del connection, cursor, statement, parameters, executemany
    metrics = get_request_metrics()
    if metrics is not None:
        metrics.start_query(execution_context)


def _finish_query(execution_context: object) -> None:
    metrics = get_request_metrics()
    if metrics is not None:
        metrics.finish_query(execution_context)


def _after_cursor_execute(
    connection: object,
    cursor: object,
    statement: str,
    parameters: object,
    execution_context: object,
    executemany: bool,
) -> None:
    del connection, cursor, statement, parameters, executemany
    _finish_query(execution_context)


def _handle_error(exception_context: object) -> None:
    execution_context = getattr(exception_context, "execution_context", None)
    if execution_context is not None:
        _finish_query(execution_context)


def register_query_monitoring(target_engine: Engine) -> None:
    """Attach the request query timing hooks to an engine."""

    event.listen(target_engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(target_engine, "after_cursor_execute", _after_cursor_execute)
    event.listen(target_engine, "handle_error", _handle_error)


register_query_monitoring(engine)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
