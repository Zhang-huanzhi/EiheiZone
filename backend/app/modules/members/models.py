"""Database models for Family Member profiles, customization, albums, and story photos."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for Member audit fields."""

    return datetime.now(UTC)


class MemberAccentColor(str, Enum):
    """Curated accent color palette for a member space."""

    DEEP_BLUE = "deep_blue"
    WARM_ORANGE = "warm_orange"
    FOREST_GREEN = "forest_green"
    BURGUNDY = "burgundy"
    ELEGANT_GRAY = "elegant_gray"


class MemberLayoutPreference(str, Enum):
    """Preset page layout emphasis for a member space."""

    PROFILE_FIRST = "profile_first"
    GALLERY_FIRST = "gallery_first"


class MemberImageStatus(str, Enum):
    """Track uploaded member images before and after association."""

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


class MemberImage(Base):
    """One processed WebP uploaded for a member avatar, banner, or gallery photo."""

    __tablename__ = "member_images"
    __table_args__ = (
        CheckConstraint("file_size BETWEEN 1 AND 5242880", name="member_image_file_size_range"),
        CheckConstraint("width > 0 AND height > 0", name="member_image_dimensions_positive"),
        Index("ix_member_images_target_user_id", "target_user_id"),
        Index("ix_member_images_status_created_at", "status", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    target_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    storage_key: Mapped[str] = mapped_column(String(300), unique=True)
    mime_type: Mapped[str] = mapped_column(
        String(40), default="image/webp", server_default=text("'image/webp'")
    )
    file_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    status: Mapped[MemberImageStatus] = mapped_column(
        SqlEnum(
            MemberImageStatus,
            name="member_image_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=MemberImageStatus.PENDING,
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
    cleanup_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_cleanup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_cleanup_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[object] = relationship("User", foreign_keys=[owner_id])
    target_user: Mapped[object] = relationship("User", foreign_keys=[target_user_id])

    @property
    def url(self) -> str:
        return f"/api/v1/media/member-images/{self.id}"


class MemberProfile(Base):
    """Structured bio, Q&A tags, and theme customization for one active User."""

    __tablename__ = "member_profiles"
    __table_args__ = (
        CheckConstraint(
            "family_title IS NULL OR char_length(btrim(family_title)) BETWEEN 1 AND 40",
            name="member_profile_family_title_length",
        ),
        CheckConstraint(
            "status_text IS NULL OR char_length(btrim(status_text)) BETWEEN 1 AND 120",
            name="member_profile_status_text_length",
        ),
        CheckConstraint(
            "hobbies IS NULL OR char_length(btrim(hobbies)) BETWEEN 1 AND 200",
            name="member_profile_hobbies_length",
        ),
        CheckConstraint(
            "skills IS NULL OR char_length(btrim(skills)) BETWEEN 1 AND 200",
            name="member_profile_skills_length",
        ),
        CheckConstraint(
            "location IS NULL OR char_length(btrim(location)) BETWEEN 1 AND 100",
            name="member_profile_location_length",
        ),
        CheckConstraint(
            "about_me IS NULL OR (char_length(about_me) <= 500 AND char_length(btrim(about_me)) >= 1)",
            name="member_profile_about_me_length",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    family_title: Mapped[str | None] = mapped_column(String(40), nullable=True)
    identity_tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        server_default=text("'[]'"),
    )
    status_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hobbies: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    about_me: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_image_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("member_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    banner_image_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("member_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    accent_color: Mapped[MemberAccentColor] = mapped_column(
        SqlEnum(
            MemberAccentColor,
            name="member_accent_color",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=MemberAccentColor.DEEP_BLUE,
        server_default=text("'deep_blue'"),
    )
    layout_preference: Mapped[MemberLayoutPreference] = mapped_column(
        SqlEnum(
            MemberLayoutPreference,
            name="member_layout_preference",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=MemberLayoutPreference.PROFILE_FIRST,
        server_default=text("'profile_first'"),
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

    user: Mapped[object] = relationship("User")
    avatar_image: Mapped[MemberImage | None] = relationship(
        "MemberImage", foreign_keys=[avatar_image_id]
    )
    banner_image: Mapped[MemberImage | None] = relationship(
        "MemberImage", foreign_keys=[banner_image_id]
    )


class MemberAlbum(Base):
    """A themed photo album belonging to one family member space."""

    __tablename__ = "member_albums"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 60",
            name="member_album_title_length",
        ),
        CheckConstraint(
            "description IS NULL OR (char_length(description) <= 300 AND char_length(btrim(description)) >= 1)",
            name="member_album_description_length",
        ),
        CheckConstraint("position >= 0", name="member_album_position_non_negative"),
        Index(
            "ix_member_albums_user_position",
            "user_id",
            "position",
            text("created_at DESC"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cover_image_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("member_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[object] = relationship("User")
    cover_image: Mapped[MemberImage | None] = relationship(
        "MemberImage", foreign_keys=[cover_image_id]
    )
    photos: Mapped[list["MemberPhoto"]] = relationship(
        "MemberPhoto",
        back_populates="album",
        order_by="MemberPhoto.position.asc(), MemberPhoto.created_at.desc(), MemberPhoto.id.desc()",
        passive_deletes="all",
    )


class MemberPhoto(Base):
    """One gallery photo with optional era/time label, location, and story."""

    __tablename__ = "member_photos"
    __table_args__ = (
        CheckConstraint(
            "taken_at_label IS NULL OR char_length(btrim(taken_at_label)) BETWEEN 1 AND 60",
            name="member_photo_taken_at_label_length",
        ),
        CheckConstraint(
            "location IS NULL OR char_length(btrim(location)) BETWEEN 1 AND 100",
            name="member_photo_location_length",
        ),
        CheckConstraint(
            "story IS NULL OR (char_length(story) <= 500 AND char_length(btrim(story)) >= 1)",
            name="member_photo_story_length",
        ),
        CheckConstraint("position >= 0", name="member_photo_position_non_negative"),
        Index(
            "ix_member_photos_album_position",
            "album_id",
            "position",
            text("created_at DESC"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    album_id: Mapped[UUID] = mapped_column(ForeignKey("member_albums.id", ondelete="CASCADE"))
    image_id: Mapped[UUID] = mapped_column(
        ForeignKey("member_images.id", ondelete="RESTRICT"),
        unique=True,
    )
    taken_at_label: Mapped[str | None] = mapped_column(String(60), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    story: Mapped[str | None] = mapped_column(String(500), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    album: Mapped[MemberAlbum] = relationship("MemberAlbum", back_populates="photos")
    image: Mapped[MemberImage] = relationship("MemberImage")
