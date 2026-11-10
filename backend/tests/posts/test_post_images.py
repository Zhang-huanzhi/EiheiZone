from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import UploadFile
from PIL import Image
from sqlalchemy.orm import Session

import app.modules.posts.image_service as image_service
from app.core.errors import AppError
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.posts.models import Post, PostImageStatus, PostVisibility
from app.modules.posts.schemas import PostCreate, PostUpdate
from app.modules.posts.service import create_post, remove_post, update_post


PASSWORD = "test-password-123"


def make_image_upload(*, image_format: str = "JPEG", size: tuple[int, int] = (120, 80)) -> UploadFile:
    data = BytesIO()
    Image.new("RGB", size, "#2f6f62").save(data, format=image_format)
    data.seek(0)
    return UploadFile(filename=f"test.{image_format.lower()}", file=data)


def create_owner(test_session: Session):
    return create_user(
        test_session,
        login_name=f"post-image-owner-{uuid4().hex}",
        display_name="Post Image Owner",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )


def create_family(test_session: Session):
    return create_user(
        test_session,
        login_name=f"post-image-family-{uuid4().hex}",
        display_name="Post Image Family",
        role=UserRole.FAMILY,
        plain_password=PASSWORD,
    )


def test_upload_processes_webp_and_attaches_in_order(
    test_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(image_service, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    owner = create_owner(test_session)
    first = image_service.upload_image(test_session, user=owner, upload=make_image_upload())
    second = image_service.upload_image(test_session, user=owner, upload=make_image_upload(image_format="PNG"))

    post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(
            title="Images",
            body="Image body",
            visibility=PostVisibility.PUBLIC,
            image_ids=[second.id, first.id],
        ),
    )

    assert [image.id for image in post.images] == [second.id, first.id]
    assert [image.position for image in post.images] == [0, 1]
    assert all(image.status is PostImageStatus.ATTACHED for image in (first, second))
    assert all(image_service.image_path(image).read_bytes()[:4] == b"RIFF" for image in (first, second))


def test_remove_post_deletes_attached_file(
    test_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(image_service, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    owner = create_owner(test_session)
    image = image_service.upload_image(test_session, user=owner, upload=make_image_upload())
    post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Delete image", body="Body", image_ids=[image.id]),
    )
    stored_path = image_service.image_path(image)
    assert stored_path.is_file()

    remove_post(test_session, user=owner, post_id=post.id)

    assert not stored_path.exists()


def test_family_can_upload_and_attach_images(
    test_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(image_service, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    family = create_family(test_session)
    image = image_service.upload_image(test_session, user=family, upload=make_image_upload())

    post = create_post(
        test_session,
        user=family,
        payload=PostCreate(title="Family image", body="Family image body", image_ids=[image.id]),
    )

    assert test_session.get(Post, post.id).author_id == family.id
    assert post.images[0].id == image.id
    assert image.owner_id == family.id


def test_owner_can_replace_post_images_and_reorder(
    test_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(image_service, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    owner = create_owner(test_session)
    first = image_service.upload_image(test_session, user=owner, upload=make_image_upload())
    second = image_service.upload_image(test_session, user=owner, upload=make_image_upload(image_format="PNG"))
    post = create_post(test_session, user=owner, payload=PostCreate(title="Edit images", body="Body", image_ids=[first.id, second.id]))
    first_path = image_service.image_path(first)

    updated = update_post(
        test_session,
        user=owner,
        post_id=post.id,
        payload=PostUpdate(image_ids=[second.id]),
    )

    assert [image.id for image in updated.images] == [second.id]
    assert not first_path.exists()


def test_upload_auto_resizes_high_resolution_and_mpo_images(
    test_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(image_service, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    owner = create_owner(test_session)

    # 5000x4000 high-resolution image (> old 4096 limit)
    high_res = image_service.upload_image(
        test_session,
        user=owner,
        upload=make_image_upload(image_format="JPEG", size=(5000, 4000)),
    )
    assert high_res.width == 2048
    assert high_res.height == 1638

    # MPO dual-camera format
    mpo_buf = BytesIO()
    im1 = Image.new("RGB", (600, 400), "#123456")
    im2 = Image.new("RGB", (300, 200), "#654321")
    im1.save(mpo_buf, format="MPO", save_all=True, append_images=[im2])
    mpo_buf.seek(0)
    mpo_img = image_service.upload_image(
        test_session,
        user=owner,
        upload=UploadFile(filename="camera.jpg", file=mpo_buf),
    )
    assert mpo_img.width == 600
    assert mpo_img.height == 400

    # HEIC disguised as .jpg returns clear Chinese error
    heic_bytes = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00heicmif1"
    with pytest.raises(AppError) as exc_info:
        image_service.upload_image(
            test_session,
            user=owner,
            upload=UploadFile(filename="id_card.jpg", file=BytesIO(heic_bytes)),
        )
    assert exc_info.value.code == "INVALID_IMAGE"
    assert "HEIC" in exc_info.value.message


def test_attach_and_replace_images_rejects_exceeding_max_limit_with_chinese_error() -> None:
    dummy_post = SimpleNamespace(images=[])
    dummy_user = SimpleNamespace(id=uuid4())

    ten_ids = [uuid4() for _ in range(10)]
    with pytest.raises(AppError) as exc_info:
        image_service.attach_images(None, user=dummy_user, post=dummy_post, image_ids=ten_ids)  # type: ignore[arg-type]
    assert exc_info.value.code == "INVALID_IMAGE_LIST"
    assert "9 张图片" in exc_info.value.message

    with pytest.raises(AppError) as exc_info_replace:
        image_service.replace_post_images(None, user=dummy_user, post=dummy_post, image_ids=ten_ids)  # type: ignore[arg-type]
    assert exc_info_replace.value.code == "INVALID_IMAGE_LIST"
    assert "9 张图片" in exc_info_replace.value.message

    # Duplicate IDs are also rejected
    duplicate_ids = [uuid4(), uuid4()]
    duplicate_ids.append(duplicate_ids[0])
    with pytest.raises(AppError) as exc_info_dup:
        image_service.attach_images(None, user=dummy_user, post=dummy_post, image_ids=duplicate_ids)  # type: ignore[arg-type]
    assert exc_info_dup.value.code == "INVALID_IMAGE_LIST"
    assert "且不能重复" in exc_info_dup.value.message
