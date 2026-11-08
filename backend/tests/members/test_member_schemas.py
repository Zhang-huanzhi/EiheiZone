"""Unit tests for Family Member Space Pydantic schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.members.models import MemberAccentColor, MemberLayoutPreference
from app.modules.members.schemas import (
    MemberAlbumCreate,
    MemberAlbumUpdate,
    MemberPhotoBatchCreate,
    MemberPhotoItemCreate,
    MemberPhotoUpdate,
    MemberProfileUpdate,
)


def test_member_profile_update_normalizes_blank_fields_and_deduplicates_tags() -> None:
    payload = MemberProfileUpdate(
        family_title="  老爸  ",
        identity_tags=[" 退休人员 ", "钓鱼达人", "退休人员", "   "],
        status_text="   ",
        hobbies="  钓鱼、养花  ",
        skills="",
        location=" 上海 ",
        about_me="   ",
        accent_color=MemberAccentColor.FOREST_GREEN,
        layout_preference=MemberLayoutPreference.GALLERY_FIRST,
    )

    assert payload.family_title == "老爸"
    assert payload.identity_tags == ["退休人员", "钓鱼达人"]
    assert payload.status_text is None
    assert payload.hobbies == "钓鱼、养花"
    assert payload.skills is None
    assert payload.location == "上海"
    assert payload.about_me is None
    assert payload.accent_color is MemberAccentColor.FOREST_GREEN
    assert payload.layout_preference is MemberLayoutPreference.GALLERY_FIRST


def test_member_profile_update_rejects_excessive_tags_or_about_me_length() -> None:
    with pytest.raises(ValidationError):
        MemberProfileUpdate(identity_tags=["a", "b", "c", "d", "e", "f"])

    with pytest.raises(ValidationError):
        MemberProfileUpdate(identity_tags=["x" * 21])

    with pytest.raises(ValidationError):
        MemberProfileUpdate(about_me="字" * 501)


def test_member_album_create_and_update_validate_fields() -> None:
    created = MemberAlbumCreate(title="  当兵回忆  ", description="  ")
    assert created.title == "当兵回忆"
    assert created.description is None

    with pytest.raises(ValidationError):
        MemberAlbumCreate(title="   ")

    with pytest.raises(ValidationError):
        MemberAlbumUpdate()

    with pytest.raises(ValidationError):
        MemberAlbumUpdate(title=None)


def test_member_photo_batch_and_update_validate_uniqueness_and_lengths() -> None:
    shared_id = uuid4()
    with pytest.raises(ValidationError):
        MemberPhotoBatchCreate(
            photos=[
                MemberPhotoItemCreate(image_id=shared_id),
                MemberPhotoItemCreate(image_id=shared_id),
            ]
        )

    with pytest.raises(ValidationError):
        MemberPhotoItemCreate(image_id=uuid4(), story="故" * 501)

    with pytest.raises(ValidationError):
        MemberPhotoUpdate()

    updated = MemberPhotoUpdate(
        taken_at_label=" 1988年秋 ",
        location=" 八达岭长城 ",
        story="当年第一次去北京",
    )
    assert updated.taken_at_label == "1988年秋"
    assert updated.location == "八达岭长城"
    assert updated.story == "当年第一次去北京"
