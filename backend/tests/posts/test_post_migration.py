from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_post_migration_downgrades_to_auth_and_upgrades_to_head(
    test_engine: Engine,
) -> None:
    """Verify the Post revision can be safely removed and restored in the test database."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "e3c19e1264ae")

    assert "posts" not in inspect(test_engine).get_table_names()

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    cleanup_columns = {column["name"] for column in inspector.get_columns("post_images")}
    cleanup_tables = set(inspector.get_table_names())
    columns = {column["name"] for column in inspector.get_columns("posts")}
    comment_columns = {column["name"] for column in inspector.get_columns("post_comments")}
    foreign_keys = inspector.get_foreign_keys("posts")
    indexes = inspector.get_indexes("posts")
    comment_foreign_keys = inspector.get_foreign_keys("post_comments")
    comment_indexes = inspector.get_indexes("post_comments")

    assert {"id", "author_id", "title", "body", "visibility", "created_at", "updated_at"}.issubset(columns)
    assert any(key["options"].get("ondelete") == "RESTRICT" for key in foreign_keys)
    assert any(index["name"] == "ix_posts_visibility_created_at" for index in indexes)
    assert {"id", "post_id", "author_id", "body", "created_at"}.issubset(comment_columns)
    assert any(key["options"].get("ondelete") == "CASCADE" for key in comment_foreign_keys)
    assert any(key["options"].get("ondelete") == "RESTRICT" for key in comment_foreign_keys)
    assert any(index["name"] == "ix_post_comments_post_created_at" for index in comment_indexes)
    assert {"cleanup_attempts", "last_cleanup_at", "last_cleanup_error"}.issubset(cleanup_columns)
    assert "media_cleanup_runs" in cleanup_tables
