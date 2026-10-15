from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_notification_migration_downgrades_to_post_images_and_upgrades_to_head(
    test_engine: Engine,
) -> None:
    """Verify the Notification revision can be safely removed and restored in the test database."""

    config = Config("alembic.ini")
    config.cmd_opts = SimpleNamespace(x=["database=test"])
    command.downgrade(config, "c18f6a72d901")

    inspector = inspect(test_engine)
    tables_after_downgrade = set(inspector.get_table_names())
    assert "wechat_bindings" not in tables_after_downgrade
    assert "wechat_binding_codes" not in tables_after_downgrade
    assert "notification_outbox" not in tables_after_downgrade
    assert "post_images" in tables_after_downgrade

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    tables_after_upgrade = set(inspector.get_table_names())
    assert {"wechat_bindings", "wechat_binding_codes", "notification_outbox"}.issubset(
        tables_after_upgrade
    )

    outbox_columns = {
        column["name"] for column in inspector.get_columns("notification_outbox")
    }
    assert {
        "id",
        "event_type",
        "aggregate_id",
        "recipient_user_id",
        "channel",
        "status",
        "attempts",
        "next_attempt_at",
        "sent_at",
        "provider_message_id",
        "last_error",
        "created_at",
    }.issubset(outbox_columns)

    unique_constraints = inspector.get_unique_constraints("notification_outbox")
    assert any(
        constraint["name"] == "uq_notification_event_recipient_channel"
        for constraint in unique_constraints
    )
    indexes = inspector.get_indexes("notification_outbox")
    assert any(index["name"] == "ix_notification_outbox_due" for index in indexes)
