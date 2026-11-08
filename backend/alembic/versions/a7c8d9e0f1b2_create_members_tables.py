"""create member spaces tables

Revision ID: a7c8d9e0f1b2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-08 19:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c8d9e0f1b2"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "member_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=300), nullable=False),
        sa.Column(
            "mime_type",
            sa.String(length=40),
            server_default=sa.text("'image/webp'"),
            nullable=False,
        ),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "attached",
                "cleanup_pending",
                name="member_image_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'pending'"),
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
        sa.Column("cleanup_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_cleanup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_cleanup_error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "file_size BETWEEN 1 AND 5242880",
            name=op.f("ck_member_images_member_image_file_size_range"),
        ),
        sa.CheckConstraint(
            "width > 0 AND height > 0",
            name=op.f("ck_member_images_member_image_dimensions_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_member_images_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["users.id"],
            name=op.f("fk_member_images_target_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_images")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_member_images_storage_key")),
    )
    op.create_index(
        "ix_member_images_target_user_id",
        "member_images",
        ["target_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_member_images_status_created_at",
        "member_images",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "member_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_title", sa.String(length=40), nullable=True),
        sa.Column(
            "identity_tags",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("status_text", sa.String(length=120), nullable=True),
        sa.Column("hobbies", sa.String(length=200), nullable=True),
        sa.Column("skills", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("about_me", sa.Text(), nullable=True),
        sa.Column("avatar_image_id", sa.Uuid(), nullable=True),
        sa.Column("banner_image_id", sa.Uuid(), nullable=True),
        sa.Column(
            "accent_color",
            sa.Enum(
                "deep_blue",
                "warm_orange",
                "forest_green",
                "burgundy",
                "elegant_gray",
                name="member_accent_color",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'deep_blue'"),
            nullable=False,
        ),
        sa.Column(
            "layout_preference",
            sa.Enum(
                "profile_first",
                "gallery_first",
                name="member_layout_preference",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'profile_first'"),
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
            "family_title IS NULL OR char_length(btrim(family_title)) BETWEEN 1 AND 40",
            name=op.f("ck_member_profiles_member_profile_family_title_length"),
        ),
        sa.CheckConstraint(
            "status_text IS NULL OR char_length(btrim(status_text)) BETWEEN 1 AND 120",
            name=op.f("ck_member_profiles_member_profile_status_text_length"),
        ),
        sa.CheckConstraint(
            "hobbies IS NULL OR char_length(btrim(hobbies)) BETWEEN 1 AND 200",
            name=op.f("ck_member_profiles_member_profile_hobbies_length"),
        ),
        sa.CheckConstraint(
            "skills IS NULL OR char_length(btrim(skills)) BETWEEN 1 AND 200",
            name=op.f("ck_member_profiles_member_profile_skills_length"),
        ),
        sa.CheckConstraint(
            "location IS NULL OR char_length(btrim(location)) BETWEEN 1 AND 100",
            name=op.f("ck_member_profiles_member_profile_location_length"),
        ),
        sa.CheckConstraint(
            "about_me IS NULL OR (char_length(about_me) <= 500 AND char_length(btrim(about_me)) >= 1)",
            name=op.f("ck_member_profiles_member_profile_about_me_length"),
        ),
        sa.ForeignKeyConstraint(
            ["avatar_image_id"],
            ["member_images.id"],
            name=op.f("fk_member_profiles_avatar_image_id_member_images"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["banner_image_id"],
            ["member_images.id"],
            name=op.f("fk_member_profiles_banner_image_id_member_images"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_member_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_member_profiles")),
    )

    op.create_table(
        "member_albums",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("cover_image_id", sa.Uuid(), nullable=True),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
            "char_length(btrim(title)) BETWEEN 1 AND 60",
            name=op.f("ck_member_albums_member_album_title_length"),
        ),
        sa.CheckConstraint(
            "description IS NULL OR (char_length(description) <= 300 AND char_length(btrim(description)) >= 1)",
            name=op.f("ck_member_albums_member_album_description_length"),
        ),
        sa.CheckConstraint(
            "position >= 0",
            name=op.f("ck_member_albums_member_album_position_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["cover_image_id"],
            ["member_images.id"],
            name=op.f("fk_member_albums_cover_image_id_member_images"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_member_albums_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_albums")),
    )
    op.create_index(
        "ix_member_albums_user_position",
        "member_albums",
        ["user_id", "position", sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "member_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("album_id", sa.Uuid(), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("taken_at_label", sa.String(length=60), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("story", sa.String(length=500), nullable=True),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
            "taken_at_label IS NULL OR char_length(btrim(taken_at_label)) BETWEEN 1 AND 60",
            name=op.f("ck_member_photos_member_photo_taken_at_label_length"),
        ),
        sa.CheckConstraint(
            "location IS NULL OR char_length(btrim(location)) BETWEEN 1 AND 100",
            name=op.f("ck_member_photos_member_photo_location_length"),
        ),
        sa.CheckConstraint(
            "story IS NULL OR (char_length(story) <= 500 AND char_length(btrim(story)) >= 1)",
            name=op.f("ck_member_photos_member_photo_story_length"),
        ),
        sa.CheckConstraint(
            "position >= 0",
            name=op.f("ck_member_photos_member_photo_position_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["member_albums.id"],
            name=op.f("fk_member_photos_album_id_member_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["member_images.id"],
            name=op.f("fk_member_photos_image_id_member_images"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_photos")),
        sa.UniqueConstraint("image_id", name=op.f("uq_member_photos_image_id")),
    )
    op.create_index(
        "ix_member_photos_album_position",
        "member_photos",
        ["album_id", "position", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_member_photos_album_position", table_name="member_photos")
    op.drop_table("member_photos")
    op.drop_index("ix_member_albums_user_position", table_name="member_albums")
    op.drop_table("member_albums")
    op.drop_table("member_profiles")
    op.drop_index("ix_member_images_status_created_at", table_name="member_images")
    op.drop_index("ix_member_images_target_user_id", table_name="member_images")
    op.drop_table("member_images")
