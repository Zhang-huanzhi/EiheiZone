from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_expenditure_migration_downgrades_to_qas_and_upgrades_to_head() -> None:
    """Verify the Expenditure revision can be safely removed and restored."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "5c9db2e6a741")

    engine = create_engine(get_settings().test_database_url)
    try:
        inspector = inspect(engine)
        assert "expenditures" not in inspector.get_table_names()
        assert "qas" in inspector.get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(get_settings().test_database_url)
    try:
        inspector = inspect(engine)
        columns = {column["name"]: column for column in inspector.get_columns("expenditures")}
        foreign_keys = inspector.get_foreign_keys("expenditures")
        checks = inspector.get_check_constraints("expenditures")
        indexes = inspector.get_indexes("expenditures")

        assert columns["spent_on"]["type"].__class__.__name__ == "DATE"
        assert columns["amount"]["type"].precision == 18
        assert columns["amount"]["type"].scale == 4
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"
        assert any(check["name"] == "ck_expenditures_expenditure_amount_positive" for check in checks)
        assert any(index["name"] == "ix_expenditures_spent_on" for index in indexes)
    finally:
        engine.dispose()
