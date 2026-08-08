"""create post images

Revision ID: c18f6a72d901
Revises: b73f8e21c4d6
Create Date: 2026-08-07 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c18f6a72d901"
down_revision: Union[str, Sequence[str], None] = "b73f8e21c4d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=300), nullable=False),
        sa.Column("mime_type", sa.String(length=40), server_default=sa.text("'image/webp'"), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "attached", "cleanup_pending", name="post_image_status", native_enum=False, create_constraint=True),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("position BETWEEN 0 AND 8", name=op.f("ck_post_images_post_image_position_range")),
        sa.CheckConstraint("file_size BETWEEN 1 AND 5242880", name=op.f("ck_post_images_post_image_file_size_range")),
        sa.CheckConstraint("width > 0 AND height > 0", name=op.f("ck_post_images_post_image_dimensions_positive")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_post_images_owner_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name=op.f("fk_post_images_post_id_posts"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_post_images")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_post_images_storage_key")),
    )
    op.create_index("ix_post_images_post_position", "post_images", ["post_id", "position"], unique=False)
    op.create_index("ix_post_images_status_created_at", "post_images", ["status", sa.text("created_at DESC")], unique=False)


def downgrade() -> None:
    op.drop_index("ix_post_images_status_created_at", table_name="post_images")
    op.drop_index("ix_post_images_post_position", table_name="post_images")
    op.drop_table("post_images")
