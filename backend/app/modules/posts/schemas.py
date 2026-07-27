"""Client-safe input and output schemas for Post endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.posts.models import PostVisibility


MAX_TITLE_LENGTH = 120
MAX_BODY_LENGTH = 10000


def _normalize_title(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Title must not be blank")
    if len(normalized) > MAX_TITLE_LENGTH:
        raise ValueError("Title must contain at most 120 characters")
    return normalized


def _validate_body(value: str) -> str:
    if not value.strip():
        raise ValueError("Body must not be blank")
    if len(value) > MAX_BODY_LENGTH:
        raise ValueError("Body must contain at most 10000 characters")
    return value


class PostCreate(BaseModel):
    """Accept the fields Owner may set when publishing a post."""

    title: str
    body: str
    visibility: PostVisibility = PostVisibility.FAMILY

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return _normalize_title(value)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return _validate_body(value)


class PostUpdate(BaseModel):
    """Accept a non-empty partial update for an existing post."""

    title: str | None = None
    body: str | None = None
    visibility: PostVisibility | None = None

    @field_validator("title")
    @classmethod
    def normalize_optional_title(cls, value: str | None) -> str | None:
        return None if value is None else _normalize_title(value)

    @field_validator("body")
    @classmethod
    def validate_optional_body(cls, value: str | None) -> str | None:
        return None if value is None else _validate_body(value)

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> "PostUpdate":
        allowed_fields = {"title", "body", "visibility"}
        supplied_fields = self.model_fields_set & allowed_fields
        if not supplied_fields:
            raise ValueError("At least one Post field must be supplied")
        for field_name in supplied_fields:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null")
        return self


class PostResponse(BaseModel):
    """Return only Post data that pages need to render."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    body: str = Field(min_length=1, max_length=MAX_BODY_LENGTH)
    visibility: PostVisibility
    created_at: datetime
    updated_at: datetime
