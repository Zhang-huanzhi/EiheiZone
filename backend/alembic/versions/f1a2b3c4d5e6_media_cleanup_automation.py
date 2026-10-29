"""add media cleanup operation tracking and retry metadata

Revision ID: f1a2b3c4d5e6
Revises: e4f5a6b7c8d9
Create Date: 2026-10-28 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("post_images", sa.Column("cleanup_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("post_images", sa.Column("last_cleanup_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("post_images", sa.Column("last_cleanup_error", sa.Text(), nullable=True))
    op.create_table(
        "media_cleanup_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dry_run", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("scan_orphans", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'running'"), nullable=False),
        sa.Column("pending_candidates", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("orphan_candidates", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("files_deleted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("records_deleted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_cleanup_runs")),
    )
    op.create_index("ix_media_cleanup_runs_finished_at", "media_cleanup_runs", [sa.text("finished_at DESC")], unique=False)


def downgrade() -> None:
    op.drop_index("ix_media_cleanup_runs_finished_at", table_name="media_cleanup_runs")
    op.drop_table("media_cleanup_runs")
    op.drop_column("post_images", "last_cleanup_error")
    op.drop_column("post_images", "last_cleanup_at")
    op.drop_column("post_images", "cleanup_attempts")
