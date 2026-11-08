from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.core.config import BACKEND_DIRECTORY


def test_member_migration_downgrades_and_upgrades_to_head(
    test_engine: Engine,
) -> None:
    """Verify the Member Spaces revision can be safely removed and restored."""

    config = Config(str(BACKEND_DIRECTORY / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "f1a2b3c4d5e6")

    tables_before = set(inspect(test_engine).get_table_names())
    assert "member_images" not in tables_before
    assert "member_profiles" not in tables_before
    assert "member_albums" not in tables_before
    assert "member_photos" not in tables_before

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    tables_after = set(inspector.get_table_names())

    assert {
        "member_images",
        "member_profiles",
        "member_albums",
        "member_photos",
    }.issubset(tables_after)

    profile_columns = {col["name"] for col in inspector.get_columns("member_profiles")}
    album_columns = {col["name"] for col in inspector.get_columns("member_albums")}
    photo_columns = {col["name"] for col in inspector.get_columns("member_photos")}

    assert {
        "user_id",
        "family_title",
        "identity_tags",
        "status_text",
        "hobbies",
        "skills",
        "location",
        "about_me",
        "avatar_image_id",
        "banner_image_id",
        "accent_color",
        "layout_preference",
    }.issubset(profile_columns)
    assert {"id", "user_id", "title", "description", "cover_image_id", "position"}.issubset(
        album_columns
    )
    assert {"id", "album_id", "image_id", "taken_at_label", "location", "story", "position"}.issubset(
        photo_columns
    )
