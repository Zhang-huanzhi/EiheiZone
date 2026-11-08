"""Tests for Member Space companion thumbnails, on-demand generation, and variant serving."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

import app.core.security as security
import app.modules.auth.dependencies as auth_dependencies
import app.modules.auth.router as auth_router
import app.modules.members.image_service as member_image_service
import app.modules.posts.image_service as post_image_service
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import create_user
from app.modules.members.image_service import (
    delete_detached_member_images,
    get_or_create_member_image_thumbnail,
    member_image_path,
    member_image_thumbnail_path,
)
from app.modules.members.models import MemberImage, MemberImageStatus
from app.modules.members.schemas import MemberImageResponse
from app.modules.posts.image_service import cleanup_orphan_images

PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def configure_member_test_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> SimpleNamespace:
    settings = SimpleNamespace(
        app_origin=ORIGIN,
        csrf_secret="test-csrf-secret-with-at-least-thirty-two-characters",
        csrf_token_ttl_seconds=3600,
        session_cookie_name="pfp_session",
        csrf_cookie_name="pfp_csrf",
        cookie_secure=False,
        session_ttl_days=30,
        media_root=tmp_path,
    )

    def get_test_settings() -> SimpleNamespace:
        return settings

    monkeypatch.setattr(security, "get_settings", get_test_settings)
    monkeypatch.setattr(auth_dependencies, "get_settings", get_test_settings)
    monkeypatch.setattr(auth_router, "get_settings", get_test_settings)
    monkeypatch.setattr(member_image_service, "get_settings", get_test_settings)
    monkeypatch.setattr(post_image_service, "get_settings", get_test_settings)
    return settings


def make_test_image_bytes(width: int = 1200, height: int = 800) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(120, 80, 200)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_member_image_thumbnail_path_resolution(tmp_path: Path) -> None:
    img_id = uuid4()
    storage_key = f"members/2026/11/{img_id}.webp"
    image = MemberImage(
        id=img_id,
        storage_key=storage_key,
        mime_type="image/webp",
        file_size=1234,
        width=1200,
        height=800,
        status=MemberImageStatus.PENDING,
    )
    thumb_path = member_image_thumbnail_path(image)
    assert thumb_path.name == f"{img_id}_thumb.webp"
    assert image.thumbnail_url == f"/api/v1/media/member-images/{img_id}?variant=thumb"


def test_get_or_create_thumbnail_generates_and_caches_on_disk(tmp_path: Path) -> None:
    img_id = uuid4()
    storage_key = f"members/2026/11/{img_id}.webp"
    image = MemberImage(
        id=img_id,
        storage_key=storage_key,
        mime_type="image/webp",
        file_size=1234,
        width=1600,
        height=1200,
        status=MemberImageStatus.PENDING,
    )

    # Save original image file to media_root
    full_path = tmp_path / storage_key
    full_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1600, 1200), color=(10, 20, 30)).save(full_path, format="WEBP")

    thumb_path = member_image_thumbnail_path(image)
    assert not thumb_path.is_file()

    # Generate thumbnail
    res_path = get_or_create_member_image_thumbnail(image)
    assert res_path == thumb_path
    assert thumb_path.is_file()

    with Image.open(thumb_path) as thumb_img:
        w, h = thumb_img.size
        assert max(w, h) == 480
        assert w == 480
        assert h == 360

    # Second call should reuse existing file without errors
    res_path_second = get_or_create_member_image_thumbnail(image)
    assert res_path_second == thumb_path


def test_member_image_response_schema_serialization() -> None:
    img_id = uuid4()
    storage_key = f"members/2026/11/{img_id}.webp"
    image = MemberImage(
        id=img_id,
        storage_key=storage_key,
        mime_type="image/webp",
        file_size=5432,
        width=800,
        height=600,
        status=MemberImageStatus.ATTACHED,
    )
    res = MemberImageResponse.model_validate(image)
    assert res.id == img_id
    assert res.url == f"/api/v1/media/member-images/{img_id}"
    assert res.thumbnail_url == f"/api/v1/media/member-images/{img_id}?variant=thumb"
    assert res.width == 800
    assert res.height == 600


def create_member_account(
    test_session: Session,
    *,
    role: UserRole,
    display_name: str,
) -> User:
    login_name = f"member-{role.value}-{uuid4().hex[:10]}"
    return create_user(
        test_session,
        login_name=login_name,
        display_name=display_name,
        role=role,
        plain_password=PASSWORD,
    )


def login_with_csrf(client: TestClient, login_name: str) -> str:
    client.cookies.clear()
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": login_name, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_upload_generates_companion_thumbnail(
    client: TestClient,
    test_session: Session,
) -> None:
    family = create_member_account(test_session, role=UserRole.FAMILY, display_name="Family Member")
    csrf_token = login_with_csrf(client, family.login_name)

    image_bytes = make_test_image_bytes(1200, 800)
    upload_res = client.post(
        f"/api/v1/members/{family.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
    )
    assert upload_res.status_code == 201
    data = upload_res.json()
    image_id = data["id"]
    assert "thumbnail_url" in data
    assert f"/api/v1/media/member-images/{image_id}?variant=thumb" == data["thumbnail_url"]

    # Verify both files exist on disk
    image_record = test_session.get(MemberImage, image_id)
    assert image_record is not None
    full_path = member_image_path(image_record)
    thumb_path = member_image_thumbnail_path(image_record)
    assert full_path.is_file()
    assert thumb_path.is_file()

    # Verify thumbnail size
    with Image.open(thumb_path) as thumb_img:
        w, h = thumb_img.size
        assert max(w, h) <= 480


def test_get_member_image_serves_thumb_and_full_variants(
    client: TestClient,
    test_session: Session,
) -> None:
    family = create_member_account(test_session, role=UserRole.FAMILY, display_name="Family Member")
    csrf_token = login_with_csrf(client, family.login_name)

    image_bytes = make_test_image_bytes(1600, 1000)
    upload_res = client.post(
        f"/api/v1/members/{family.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
    )
    image_id = upload_res.json()["id"]

    # Request default (full)
    full_res = client.get(f"/api/v1/media/member-images/{image_id}")
    assert full_res.status_code == 200
    assert full_res.headers["Cache-Control"].lower() == "private, no-store"
    with Image.open(BytesIO(full_res.content)) as full_img:
        assert full_img.size == (1600, 1000)

    # Request thumb variant
    thumb_res = client.get(f"/api/v1/media/member-images/{image_id}?variant=thumb")
    assert thumb_res.status_code == 200
    assert thumb_res.headers["Cache-Control"].lower() == "private, no-store"
    with Image.open(BytesIO(thumb_res.content)) as thumb_img:
        w, h = thumb_img.size
        assert max(w, h) <= 480
        assert len(thumb_res.content) < len(full_res.content)


def test_on_demand_thumbnail_generation_for_legacy_photo(
    client: TestClient,
    test_session: Session,
) -> None:
    family = create_member_account(test_session, role=UserRole.FAMILY, display_name="Family Member")
    csrf_token = login_with_csrf(client, family.login_name)

    image_bytes = make_test_image_bytes(800, 600)
    upload_res = client.post(
        f"/api/v1/members/{family.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
    )
    image_id = upload_res.json()["id"]

    image_record = test_session.get(MemberImage, image_id)
    assert image_record is not None
    thumb_path = member_image_thumbnail_path(image_record)
    assert thumb_path.is_file()

    # Simulate legacy image by deleting thumbnail file
    thumb_path.unlink()
    assert not thumb_path.is_file()

    # Querying thumbnail should recreate it on-demand
    thumb_res = client.get(f"/api/v1/media/member-images/{image_id}?variant=thumb")
    assert thumb_res.status_code == 200
    assert thumb_path.is_file()
    with Image.open(thumb_path) as thumb_img:
        assert max(thumb_img.size) <= 480


def test_thumbnail_cleanup_on_image_deletion(
    test_session: Session,
) -> None:
    family = create_member_account(test_session, role=UserRole.FAMILY, display_name="Family Member")

    from fastapi import UploadFile
    upload = UploadFile(filename="test.jpg", file=BytesIO(make_test_image_bytes(500, 500)))
    image = member_image_service.upload_member_image(
        test_session,
        actor=family,
        target_user=family,
        upload=upload,
    )
    full_path = member_image_path(image)
    thumb_path = member_image_thumbnail_path(image)
    assert full_path.is_file()
    assert thumb_path.is_file()

    delete_detached_member_images(test_session, [image])
    assert not full_path.is_file()
    assert not thumb_path.is_file()


def test_orphan_scanner_preserves_member_thumbnails(
    test_session: Session,
) -> None:
    family = create_member_account(test_session, role=UserRole.FAMILY, display_name="Family Member")
    from fastapi import UploadFile
    upload = UploadFile(filename="test.jpg", file=BytesIO(make_test_image_bytes(500, 500)))
    image = member_image_service.upload_member_image(
        test_session,
        actor=family,
        target_user=family,
        upload=upload,
    )
    image.status = MemberImageStatus.ATTACHED
    test_session.commit()

    from datetime import timedelta
    stats = cleanup_orphan_images(
        test_session,
        scan_orphans=True,
        grace_period=timedelta(seconds=-1),
    )
    assert stats.orphan_candidates == 0
    full_path = member_image_path(image)
    thumb_path = member_image_thumbnail_path(image)
    assert full_path.is_file()
    assert thumb_path.is_file()
