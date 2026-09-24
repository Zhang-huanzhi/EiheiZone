from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_qa_migration_downgrades_to_posts_and_upgrades_to_head(
    test_engine: Engine,
) -> None:
    """Verify the QA revision can be safely removed and restored in the test database."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "89d3f7a41a5b")

    inspector = inspect(test_engine)
    assert "qas" not in inspector.get_table_names()
    assert "posts" in inspector.get_table_names()

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    columns = {column["name"]: column for column in inspector.get_columns("qas")}
    foreign_keys = inspector.get_foreign_keys("qas")
    checks = inspector.get_check_constraints("qas")
    indexes = inspector.get_indexes("qas")

    assert {
        "id",
        "asked_by",
        "question",
        "answer",
        "answered_by",
        "status",
        "answered_at",
        "created_at",
        "updated_at",
    }.issubset(columns)
    assert columns["status"]["type"].length == 20
    assert len(foreign_keys) == 2
    assert all(key["options"].get("ondelete") == "RESTRICT" for key in foreign_keys)
    assert any(check["name"] == "ck_qas_qa_answer_state_consistency" for check in checks)
    assert any(index["name"] == "ix_qas_status_created_at" for index in indexes)
