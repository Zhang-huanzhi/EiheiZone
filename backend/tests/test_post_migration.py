from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_post_migration_downgrades_to_auth_and_upgrades_to_head() -> None:
    """Verify the Post revision can be safely removed and restored in the test database."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "e3c19e1264ae")

    engine = create_engine(get_settings().test_database_url)
    try:
        assert "posts" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(get_settings().test_database_url)
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("posts")}
        foreign_keys = inspector.get_foreign_keys("posts")
        indexes = inspector.get_indexes("posts")

        assert {"id", "author_id", "title", "body", "visibility", "created_at", "updated_at"}.issubset(columns)
        assert any(key["options"].get("ondelete") == "RESTRICT" for key in foreign_keys)
        assert any(index["name"] == "ix_posts_visibility_created_at" for index in indexes)
    finally:
        engine.dispose()
