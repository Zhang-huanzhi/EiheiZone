"""Database model for Owner-authored status posts."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for Post audit fields."""

    return datetime.now(UTC)


class PostVisibility(str, Enum):
    """Describe which visitor groups can read a post."""

    PUBLIC = "public"
    FAMILY = "family"


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
