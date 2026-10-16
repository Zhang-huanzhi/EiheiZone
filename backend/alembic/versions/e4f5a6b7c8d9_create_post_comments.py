"""create post comments

Revision ID: e4f5a6b7c8d9
Revises: d7a1c2e3f4b5
Create Date: 2026-10-16 19:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d7a1c2e3f4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the flat text Post comment table and its access indexes."""

    op.create_table(
        "post_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(body) BETWEEN 1 AND 2000 AND char_length(btrim(body)) >= 1",
            name=op.f("ck_post_comments_post_comment_body_length"),
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            name=op.f("fk_post_comments_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_post_comments_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_post_comments")),
    )
    op.create_index(
        "ix_post_comments_post_created_at",
        "post_comments",
        ["post_id", sa.text("created_at DESC"), sa.text("id DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Remove the Post comment table introduced by this migration."""

    op.drop_index("ix_post_comments_post_created_at", table_name="post_comments")
    op.drop_table("post_comments")
