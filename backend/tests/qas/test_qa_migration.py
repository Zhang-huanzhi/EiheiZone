from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_qa_migration_downgrades_to_posts_and_upgrades_to_head(
    test_engine: Engine,
) -> None:
    """Verify the QA revisions can be safely removed and restored in the test database."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "89d3f7a41a5b")

    inspector = inspect(test_engine)
    assert "qas" not in inspector.get_table_names()
    assert "qa_answers" not in inspector.get_table_names()
    assert "posts" in inspector.get_table_names()

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    qa_columns = {column["name"]: column for column in inspector.get_columns("qas")}
    qa_answers_columns = {
        column["name"]: column for column in inspector.get_columns("qa_answers")
    }
    qa_fks = inspector.get_foreign_keys("qas")
    qa_answers_fks = inspector.get_foreign_keys("qa_answers")
    qa_indexes = inspector.get_indexes("qas")
    qa_answers_indexes = inspector.get_indexes("qa_answers")

    assert {
        "id",
        "asked_by",
        "question",
        "is_proxy",
        "status",
        "created_at",
        "updated_at",
    }.issubset(qa_columns)
    assert {
        "id",
        "qa_id",
        "author_id",
        "content",
        "is_proxy",
        "created_at",
        "updated_at",
    }.issubset(qa_answers_columns)
    assert any(fk["referred_table"] == "users" for fk in qa_fks)
    assert any(fk["referred_table"] == "qas" for fk in qa_answers_fks)
    assert any(index["name"] == "ix_qas_status_created_at" for index in qa_indexes)
    assert any(
        index["name"] == "ix_qa_answers_qa_created_at" for index in qa_answers_indexes
    )
