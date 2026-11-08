"""Client-safe input and output schemas for Family Member Space endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.auth.models import UserRole
from app.modules.members.models import MemberAccentColor, MemberLayoutPreference


MAX_FAMILY_TITLE_LENGTH = 40
MAX_IDENTITY_TAGS = 5
MAX_IDENTITY_TAG_LENGTH = 20
MAX_STATUS_TEXT_LENGTH = 120
MAX_HOBBIES_LENGTH = 200
MAX_SKILLS_LENGTH = 200
MAX_LOCATION_LENGTH = 100
MAX_ABOUT_ME_LENGTH = 500
MAX_ALBUM_TITLE_LENGTH = 60
MAX_ALBUM_DESCRIPTION_LENGTH = 300
MAX_TAKEN_AT_LABEL_LENGTH = 60
MAX_PHOTO_STORY_LENGTH = 500
MAX_BATCH_PHOTOS = 300


def _normalize_optional_single_line(value: str | None, *, max_length: int, label: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise ValueError(f"{label} must contain at most {max_length} characters")
    return normalized


def _normalize_optional_multiline(value: str | None, *, max_length: int, label: str) -> str | None:
    if value is None:
        return None
    if not value.strip():
        return None
    if len(value) > max_length:
        raise ValueError(f"{label} must contain at most {max_length} characters")
    return value


def _normalize_required_title(value: str, *, max_length: int, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{label} must contain at most {max_length} characters")
    return normalized


class MemberImageResponse(BaseModel):
    """Expose member image metadata and its permission-checked API URL."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    thumbnail_url: str
    width: int
    height: int


class MemberProfileUpdate(BaseModel):
    """Accept profile, structured Q&A bio, and theme customization fields."""

    family_title: str | None = None
    identity_tags: list[str] = Field(default_factory=list)
    status_text: str | None = None
    hobbies: str | None = None
    skills: str | None = None
    location: str | None = None
    about_me: str | None = None
    avatar_image_id: UUID | None = None
    banner_image_id: UUID | None = None
    accent_color: MemberAccentColor = MemberAccentColor.DEEP_BLUE
    layout_preference: MemberLayoutPreference = MemberLayoutPreference.PROFILE_FIRST

    @field_validator("family_title")
    @classmethod
    def validate_family_title(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_FAMILY_TITLE_LENGTH,
            label="Family title",
        )

    @field_validator("identity_tags")
    @classmethod
    def validate_identity_tags(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in values:
            tag = item.strip()
            if not tag:
                continue
            if len(tag) > MAX_IDENTITY_TAG_LENGTH:
                raise ValueError(
                    f"Each identity tag must contain at most {MAX_IDENTITY_TAG_LENGTH} characters"
                )
            if tag not in seen:
                seen.add(tag)
                cleaned.append(tag)
        if len(cleaned) > MAX_IDENTITY_TAGS:
            raise ValueError(f"At most {MAX_IDENTITY_TAGS} identity tags are allowed")
        return cleaned

    @field_validator("status_text")
    @classmethod
    def validate_status_text(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_STATUS_TEXT_LENGTH,
            label="Status text",
        )

    @field_validator("hobbies")
    @classmethod
    def validate_hobbies(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_HOBBIES_LENGTH,
            label="Hobbies",
        )

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_SKILLS_LENGTH,
            label="Skills",
        )

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_LOCATION_LENGTH,
            label="Location",
        )

    @field_validator("about_me")
    @classmethod
    def validate_about_me(cls, value: str | None) -> str | None:
        return _normalize_optional_multiline(
            value,
            max_length=MAX_ABOUT_ME_LENGTH,
            label="About me",
        )


class MemberAlbumCreate(BaseModel):
    """Accept fields to create a themed gallery album in a member space."""

    title: str
    description: str | None = None
    cover_image_id: UUID | None = None
    position: int = Field(default=0, ge=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _normalize_required_title(
            value,
            max_length=MAX_ALBUM_TITLE_LENGTH,
            label="Album title",
        )

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return _normalize_optional_multiline(
            value,
            max_length=MAX_ALBUM_DESCRIPTION_LENGTH,
            label="Album description",
        )


class MemberAlbumUpdate(BaseModel):
    """Accept a partial update for an existing member album."""

    title: str | None = None
    description: str | None = None
    cover_image_id: UUID | None = None
    position: int | None = Field(default=None, ge=0)

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_required_title(
            value,
            max_length=MAX_ALBUM_TITLE_LENGTH,
            label="Album title",
        )

    @field_validator("description")
    @classmethod
    def validate_optional_description(cls, value: str | None) -> str | None:
        return _normalize_optional_multiline(
            value,
            max_length=MAX_ALBUM_DESCRIPTION_LENGTH,
            label="Album description",
        )

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> "MemberAlbumUpdate":
        allowed_fields = {"title", "description", "cover_image_id", "position"}
        supplied_fields = self.model_fields_set & allowed_fields
        if not supplied_fields:
            raise ValueError("At least one album field must be supplied")
        for non_nullable in ("title", "position"):
            if non_nullable in supplied_fields and getattr(self, non_nullable) is None:
                raise ValueError(f"{non_nullable} must not be null")
        return self


class MemberPhotoItemCreate(BaseModel):
    """Accept one uploaded image and its story metadata for an album."""

    image_id: UUID
    taken_at_label: str | None = None
    location: str | None = None
    story: str | None = None

    @field_validator("taken_at_label")
    @classmethod
    def validate_taken_at_label(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_TAKEN_AT_LABEL_LENGTH,
            label="Taken at label",
        )

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_LOCATION_LENGTH,
            label="Photo location",
        )

    @field_validator("story")
    @classmethod
    def validate_story(cls, value: str | None) -> str | None:
        return _normalize_optional_multiline(
            value,
            max_length=MAX_PHOTO_STORY_LENGTH,
            label="Photo story",
        )


class MemberPhotoBatchCreate(BaseModel):
    """Accept 1 to 9 photos in one batch upload to an album."""

    photos: list[MemberPhotoItemCreate] = Field(min_length=1, max_length=MAX_BATCH_PHOTOS)

    @model_validator(mode="after")
    def validate_unique_images(self) -> "MemberPhotoBatchCreate":
        image_ids = [item.image_id for item in self.photos]
        if len(set(image_ids)) != len(image_ids):
            raise ValueError("Batch photo image_ids must be unique")
        return self


class MemberPhotoUpdate(BaseModel):
    """Accept story metadata or position updates for one album photo."""

    taken_at_label: str | None = None
    location: str | None = None
    story: str | None = None
    position: int | None = Field(default=None, ge=0)

    @field_validator("taken_at_label")
    @classmethod
    def validate_taken_at_label(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_TAKEN_AT_LABEL_LENGTH,
            label="Taken at label",
        )

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _normalize_optional_single_line(
            value,
            max_length=MAX_LOCATION_LENGTH,
            label="Photo location",
        )

    @field_validator("story")
    @classmethod
    def validate_story(cls, value: str | None) -> str | None:
        return _normalize_optional_multiline(
            value,
            max_length=MAX_PHOTO_STORY_LENGTH,
            label="Photo story",
        )

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> "MemberPhotoUpdate":
        allowed_fields = {"taken_at_label", "location", "story", "position"}
        supplied_fields = self.model_fields_set & allowed_fields
        if not supplied_fields:
            raise ValueError("At least one photo field must be supplied")
        if "position" in supplied_fields and self.position is None:
            raise ValueError("position must not be null")
        return self


class MemberPhotoResponse(BaseModel):
    """Return one gallery photo with its story attributes and image metadata."""

    id: UUID
    album_id: UUID
    image: MemberImageResponse
    taken_at_label: str | None
    location: str | None
    story: str | None
    position: int
    created_at: datetime
    updated_at: datetime


class MemberAlbumSummaryResponse(BaseModel):
    """Return one album summary card with cover and up to 4 preview photos."""

    id: UUID
    user_id: UUID
    title: str
    description: str | None
    cover_image: MemberImageResponse | None
    photo_count: int
    preview_photos: list[MemberPhotoResponse] = Field(default_factory=list)
    position: int
    created_at: datetime
    updated_at: datetime


class MemberAlbumDetailResponse(BaseModel):
    """Return one album with all of its ordered photos and member context."""

    id: UUID
    user_id: UUID
    member_display_name: str
    member_family_title: str
    accent_color: MemberAccentColor
    can_edit: bool
    title: str
    description: str | None
    cover_image: MemberImageResponse | None
    photo_count: int
    photos: list[MemberPhotoResponse] = Field(default_factory=list)
    position: int
    created_at: datetime
    updated_at: datetime


class MemberSummaryCardResponse(BaseModel):
    """Return one member's directory card and profile summary."""

    user_id: UUID
    display_name: str
    role: UserRole
    family_title: str
    custom_family_title: str | None
    identity_tags: list[str] = Field(default_factory=list)
    status_text: str | None
    hobbies: str | None
    skills: str | None
    location: str | None
    about_me: str | None
    avatar_image: MemberImageResponse | None
    banner_image: MemberImageResponse | None
    accent_color: MemberAccentColor
    layout_preference: MemberLayoutPreference
    album_count: int
    photo_count: int
    is_current_user: bool
    can_edit: bool
    updated_at: datetime


class MemberSpaceResponse(MemberSummaryCardResponse):
    """Return a member's full space including profile, theme, albums, and flat photos."""

    albums: list[MemberAlbumSummaryResponse] = Field(default_factory=list)
    photos: list[MemberPhotoResponse] = Field(default_factory=list)
