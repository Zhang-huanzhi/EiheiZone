"""Database model for Owner-authored status posts."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for Post audit fields."""

    return datetime.now(UTC)


class PostVisibility(str, Enum):
    """Describe which visitor groups can read a post."""

    PUBLIC = "public"
    FAMILY = "family"


class PostImageStatus(str, Enum):
    """Track uploaded images before and after Post association."""

    PENDING = "pending"
    ATTACHED = "attached"
    CLEANUP_PENDING = "cleanup_pending"


def enum_values(enum_class: type[Enum]) -> list[str]:
    """Persist string enum values instead of Python member names."""

    values: list[str] = []
    for member in enum_class:
        value = member.value
        if not isinstance(value, str):
            raise TypeError("Database enum values must be strings")
        values.append(value)
    return values


class Post(Base):
    """A short update authored and managed by an Owner."""

    __tablename__ = "posts"
    # noinspection SpellCheckingInspection
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 120",
            name="post_title_length",
        ),
        CheckConstraint(
            "char_length(body) BETWEEN 1 AND 10000 AND char_length(btrim(body)) >= 1",
            name="post_body_length",
        ),
        Index("ix_posts_visibility_created_at", "visibility", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    visibility: Mapped[PostVisibility] = mapped_column(
        SqlEnum(
            PostVisibility,
            name="post_visibility",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=PostVisibility.FAMILY,
        server_default=text("'family'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    author: Mapped[object] = relationship("User")
    images: Mapped[list["PostImage"]] = relationship(
        "PostImage",
        back_populates="post",
        order_by="PostImage.position",
        passive_deletes="all",
    )


class PostImage(Base):
    """One processed WebP uploaded by an Owner for a Post."""

    __tablename__ = "post_images"
    __table_args__ = (
        CheckConstraint("position BETWEEN 0 AND 8", name="post_image_position_range"),
        CheckConstraint("file_size BETWEEN 1 AND 5242880", name="post_image_file_size_range"),
        CheckConstraint("width > 0 AND height > 0", name="post_image_dimensions_positive"),
        Index("ix_post_images_post_position", "post_id", "position"),
        Index("ix_post_images_status_created_at", "status", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    storage_key: Mapped[str] = mapped_column(String(300), unique=True)
    mime_type: Mapped[str] = mapped_column(
        String(40), default="image/webp", server_default=text("'image/webp'")
    )
    file_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    status: Mapped[PostImageStatus] = mapped_column(
        SqlEnum(
            PostImageStatus,
            name="post_image_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=PostImageStatus.PENDING,
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    post: Mapped[Post | None] = relationship("Post", back_populates="images")
    owner: Mapped[object] = relationship("User")

    @property
    def url(self) -> str:
        return f"/api/v1/media/images/{self.id}"
