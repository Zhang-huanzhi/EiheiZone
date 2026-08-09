from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.posts.models import PostVisibility
from app.modules.posts.schemas import PostCreate, PostResponse, PostUpdate


def test_post_create_normalizes_title_and_defaults_to_family_visibility() -> None:
    payload = PostCreate(title="  Update title  ", body="Body with spaces  ")

    assert payload.title == "Update title"
    assert payload.body == "Body with spaces  "
    assert payload.visibility is PostVisibility.FAMILY


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "body": "Valid body"},
        {"title": "   ", "body": "Valid body"},
        {"title": "x" * 121, "body": "Valid body"},
        {"title": "Valid title", "body": ""},
        {"title": "Valid title", "body": "   "},
        {"title": "Valid title", "body": "x" * 10001},
        {"title": "Valid title", "body": "Valid body", "visibility": "hidden"},
    ],
)
def test_post_create_rejects_invalid_fields(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        PostCreate(**payload)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"body": None},
        {"visibility": None},
        {"title": "   "},
        {"body": "   "},
    ],
)
def test_post_update_rejects_empty_null_or_invalid_updates(payload: dict[str, str | None]) -> None:
    with pytest.raises(ValidationError):
        PostUpdate(**payload)


def test_post_update_keeps_only_supplied_fields() -> None:
    payload = PostUpdate(title="  Updated title ")

    assert payload.model_dump(exclude_unset=True) == {"title": "Updated title"}


def test_post_response_exposes_client_safe_author_fields_only() -> None:
    response = PostResponse(
        id=uuid4(),
        author_id=uuid4(),
        author_display_name="Post Author",
        title="Update",
        body="Body",
        visibility=PostVisibility.PUBLIC,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert set(response.model_dump()) == {
        "id",
        "author_id",
        "author_display_name",
        "title",
        "body",
        "visibility",
        "created_at",
        "updated_at",
        "images",
    }
