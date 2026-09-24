from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_auth_migration_upgrades_an_empty_test_database(test_engine: Engine) -> None:
    """Prove the complete migration chain can recreate Auth tables from base."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    inspector = inspect(test_engine)
    assert {"users", "sessions"}.issubset(inspector.get_table_names())
