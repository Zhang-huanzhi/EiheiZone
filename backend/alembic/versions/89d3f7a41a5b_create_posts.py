"""create posts

Revision ID: 89d3f7a41a5b
Revises: e3c19e1264ae
Create Date: 2026-07-26 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "89d3f7a41a5b"
down_revision: Union[str, Sequence[str], None] = "e3c19e1264ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the Post table, its integrity checks, and list index."""

    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "visibility",
            sa.Enum(
                "public",
                "family",
                name="post_visibility",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'family'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 120",
            name=op.f("ck_posts_post_title_length"),
        ),
        sa.CheckConstraint(
            "char_length(body) BETWEEN 1 AND 10000 AND char_length(btrim(body)) >= 1",
            name=op.f("ck_posts_post_body_length"),
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_posts_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_posts")),
    )
    op.create_index(
        "ix_posts_visibility_created_at",
        "posts",
        ["visibility", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Remove only the Post table introduced by this migration."""

    op.drop_index("ix_posts_visibility_created_at", table_name="posts")
    op.drop_table("posts")
