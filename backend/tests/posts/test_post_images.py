from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image
from sqlalchemy.orm import Session

import app.modules.posts.image_service as image_service
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.posts.models import Post, PostImageStatus, PostVisibility
from app.modules.posts.schemas import PostCreate
from app.modules.posts.service import create_post, remove_post


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
