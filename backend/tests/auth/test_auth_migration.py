from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_auth_migration_upgrades_an_empty_test_database() -> None:
    """Prove the complete migration chain can recreate Auth tables from base."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_engine(get_settings().test_database_url)
    try:
        inspector = inspect(engine)
        assert {"users", "sessions"}.issubset(inspector.get_table_names())
    finally:
        engine.dispose()
