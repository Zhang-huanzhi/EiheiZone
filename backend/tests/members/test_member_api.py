"""API, authorization, and media cleanup tests for Family Member Spaces."""

from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

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
from app.modules.members.models import MemberImage
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


def make_jpeg_bytes(width: int = 32, height: int = 20, color: str = "#355c7d") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="JPEG")
    return buffer.getvalue()


def upload_test_member_image(
    client: TestClient,
    *,
    csrf_token: str,
    target_user_id: UUID,
    filename: str = "photo.jpg",
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/members/{target_user_id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        files={"file": (filename, make_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 201
    return response.json()


def test_member_directory_places_current_user_first_and_provides_defaults(
    client: TestClient,
    test_session: Session,
) -> None:
    owner = create_member_account(test_session, role=UserRole.OWNER, display_name="张明")
    family_b = create_member_account(test_session, role=UserRole.FAMILY, display_name="张爸")

    login_with_csrf(client, family_b.login_name)
    response = client.get("/api/v1/members")
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) >= 2
    assert cards[0]["user_id"] == str(family_b.id)
    assert cards[0]["is_current_user"] is True
    assert cards[0]["can_edit"] is True
    assert cards[0]["accent_color"] == "deep_blue"
    assert cards[0]["layout_preference"] == "profile_first"

    owner_card = next(card for card in cards if card["user_id"] == str(owner.id))
    assert owner_card["is_current_user"] is False
    assert owner_card["can_edit"] is False


def test_public_cannot_access_member_spaces_or_member_images(
    client: TestClient,
    test_session: Session,
) -> None:
    member = create_member_account(test_session, role=UserRole.FAMILY, display_name="张妈")
    csrf_token = login_with_csrf(client, member.login_name)
    uploaded = upload_test_member_image(client, csrf_token=csrf_token, target_user_id=member.id)

    # Attach as avatar so it becomes ATTACHED
    profile_resp = client.put(
        f"/api/v1/members/{member.id}/profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"avatar_image_id": uploaded["id"]},
    )
    assert profile_resp.status_code == 200

    # Logout / clear cookies to simulate anonymous Public visitor
    client.cookies.clear()
    assert client.get("/api/v1/members").status_code == 401
    assert client.get(f"/api/v1/members/{member.id}").status_code == 401
    assert client.get(f"/api/v1/media/member-images/{uploaded['id']}").status_code == 404


def test_family_member_can_only_edit_own_space_and_not_others(
    client: TestClient,
    test_session: Session,
) -> None:
    father = create_member_account(test_session, role=UserRole.FAMILY, display_name="张爸")
    mother = create_member_account(test_session, role=UserRole.FAMILY, display_name="张妈")

    csrf_token = login_with_csrf(client, father.login_name)

    own_update = client.put(
        f"/api/v1/members/{father.id}/profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={
            "family_title": "老爸",
            "identity_tags": ["钓友", "大厨"],
            "status_text": "周末准备去水库钓鱼",
            "hobbies": "钓鱼、象棋",
        },
    )
    assert own_update.status_code == 200
    assert own_update.json()["family_title"] == "老爸"
    assert own_update.json()["identity_tags"] == ["钓友", "大厨"]

    forbidden_profile = client.put(
        f"/api/v1/members/{mother.id}/profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"family_title": "老妈"},
    )
    assert forbidden_profile.status_code == 403
    assert forbidden_profile.json()["error"]["code"] == "FORBIDDEN"

    forbidden_album = client.post(
        f"/api/v1/members/{mother.id}/albums",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"title": "越权相册"},
    )
    assert forbidden_album.status_code == 403


def test_owner_can_bootstrap_elder_profile_and_elder_can_batch_upload_story_photos(
    client: TestClient,
    test_session: Session,
) -> None:
    """Verify Scenario A (Owner bootstraps elder profile) and Scenario B (Story gallery)."""

    owner = create_member_account(test_session, role=UserRole.OWNER, display_name="Zzk")
    father = create_member_account(test_session, role=UserRole.FAMILY, display_name="张爸")

    owner_csrf = login_with_csrf(client, owner.login_name)
    avatar = upload_test_member_image(client, csrf_token=owner_csrf, target_user_id=father.id)
    banner = upload_test_member_image(client, csrf_token=owner_csrf, target_user_id=father.id)

    bootstrap = client.put(
        f"/api/v1/members/{father.id}/profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": owner_csrf},
        json={
            "family_title": "老爸",
            "identity_tags": ["退伍军人"],
            "status_text": "身体硬朗，每天晨练",
            "avatar_image_id": avatar["id"],
            "banner_image_id": banner["id"],
            "accent_color": "warm_orange",
            "layout_preference": "gallery_first",
        },
    )
    assert bootstrap.status_code == 200
    assert bootstrap.json()["avatar_image"]["id"] == avatar["id"]
    assert bootstrap.json()["banner_image"]["id"] == banner["id"]

    # Elder logs in, creates an album, and batch uploads 2 old photos with stories
    father_csrf = login_with_csrf(client, father.login_name)
    album_resp = client.post(
        f"/api/v1/members/{father.id}/albums",
        headers={"Origin": ORIGIN, "X-CSRF-Token": father_csrf},
        json={"title": "当兵与打拼回忆", "description": "年轻时候的老照片"},
    )
    assert album_resp.status_code == 201
    album_id = album_resp.json()["id"]

    img1 = upload_test_member_image(client, csrf_token=father_csrf, target_user_id=father.id)
    img2 = upload_test_member_image(client, csrf_token=father_csrf, target_user_id=father.id)

    batch_resp = client.post(
        f"/api/v1/members/{father.id}/albums/{album_id}/photos",
        headers={"Origin": ORIGIN, "X-CSRF-Token": father_csrf},
        json={
            "photos": [
                {
                    "image_id": img1["id"],
                    "taken_at_label": "1988年秋",
                    "location": "北京八达岭长城",
                    "story": "当年我和你妈第一次去长城",
                },
                {
                    "image_id": img2["id"],
                    "taken_at_label": "1992年夏",
                    "location": "深圳",
                    "story": "当年一穷二白，但浑身是劲",
                },
            ]
        },
    )
    assert batch_resp.status_code == 201
    album_detail = batch_resp.json()
    assert album_detail["photo_count"] == 2
    assert album_detail["cover_image"]["id"] == img1["id"]
    assert album_detail["photos"][0]["taken_at_label"] == "1988年秋"
    assert album_detail["photos"][0]["story"] == "当年我和你妈第一次去长城"

    # Verify media endpoint requires authentication and returns private, no-store
    media_resp = client.get(f"/api/v1/media/member-images/{img1['id']}")
    assert media_resp.status_code == 200
    assert media_resp.headers["cache-control"] == "private, no-store"

    # Update first photo story
    photo_id = album_detail["photos"][0]["id"]
    patch_photo = client.patch(
        f"/api/v1/members/{father.id}/albums/{album_id}/photos/{photo_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": father_csrf},
        json={"story": "1988年秋天，第一次带相机去北京八达岭长城"},
    )
    assert patch_photo.status_code == 200
    assert patch_photo.json()["story"] == "1988年秋天，第一次带相机去北京八达岭长城"

    # Delete second photo and verify count
    second_photo_id = album_detail["photos"][1]["id"]
    del_photo = client.delete(
        f"/api/v1/members/{father.id}/albums/{album_id}/photos/{second_photo_id}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": father_csrf},
    )
    assert del_photo.status_code == 204
    assert test_session.get(MemberImage, UUID(str(img2["id"]))) is None


def test_media_cleanup_preserves_attached_member_images_and_cleans_stale_pending(
    client: TestClient,
    test_session: Session,
) -> None:
    """Ensure cleanup_orphan_images never deletes attached MemberImages during orphan scan."""

    father = create_member_account(test_session, role=UserRole.FAMILY, display_name="张爸")
    csrf = login_with_csrf(client, father.login_name)

    attached_upload = upload_test_member_image(client, csrf_token=csrf, target_user_id=father.id)
    stale_upload = upload_test_member_image(client, csrf_token=csrf, target_user_id=father.id)

    client.put(
        f"/api/v1/members/{father.id}/profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        json={"avatar_image_id": attached_upload["id"]},
    )

    attached_record = test_session.get(MemberImage, UUID(str(attached_upload["id"])))
    stale_record = test_session.get(MemberImage, UUID(str(stale_upload["id"])))
    assert attached_record is not None
    assert stale_record is not None

    old_time = datetime.now(UTC) - timedelta(hours=48)
    attached_record.created_at = old_time
    stale_record.created_at = old_time
    test_session.commit()

    stats = cleanup_orphan_images(
        test_session,
        scan_orphans=True,
        grace_period=timedelta(hours=24),
    )

    assert stats.records_deleted == 1
    assert test_session.get(MemberImage, UUID(str(attached_upload["id"]))) is not None
    assert test_session.get(MemberImage, UUID(str(stale_upload["id"]))) is None


def test_member_image_upload_supports_high_res_mpo_bmp_and_rejects_heic_clearly(
    client: TestClient,
    test_session: Session,
) -> None:
    """Verify high-res photos (>4096px), MPO/BMP formats succeed, and HEIC returns friendly Chinese message."""

    member = create_member_account(test_session, role=UserRole.FAMILY, display_name="张弟")
    csrf = login_with_csrf(client, member.login_name)

    # 1. High-resolution 5000x3500 JPEG
    high_res_bytes = make_jpeg_bytes(width=5000, height=3500)
    resp_high = client.post(
        f"/api/v1/members/{member.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        files={"file": ("身份证手持.jpg", high_res_bytes, "image/jpeg")},
    )
    assert resp_high.status_code == 201
    assert resp_high.json()["width"] == 2048
    assert resp_high.json()["height"] == 1434

    # 2. MPO dual-camera JPEG
    mpo_buf = BytesIO()
    im1 = Image.new("RGB", (800, 600), "#224466")
    im2 = Image.new("RGB", (400, 300), "#664422")
    im1.save(mpo_buf, format="MPO", save_all=True, append_images=[im2])
    resp_mpo = client.post(
        f"/api/v1/members/{member.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        files={"file": ("portrait.jpg", mpo_buf.getvalue(), "image/jpeg")},
    )
    assert resp_mpo.status_code == 201
    assert resp_mpo.json()["width"] == 800

    # 3. BMP image
    bmp_buf = BytesIO()
    Image.new("RGB", (200, 150), "#336699").save(bmp_buf, format="BMP")
    resp_bmp = client.post(
        f"/api/v1/members/{member.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        files={"file": ("scan.bmp", bmp_buf.getvalue(), "image/bmp")},
    )
    assert resp_bmp.status_code == 201

    # 4. HEIC disguised as .jpg
    heic_bytes = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00heicmif1"
    resp_heic = client.post(
        f"/api/v1/members/{member.id}/uploads/image",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        files={"file": ("iphone_id.jpg", heic_bytes, "image/jpeg")},
    )
    assert resp_heic.status_code == 400
    assert resp_heic.json()["error"]["code"] == "INVALID_IMAGE"
    assert "HEIC" in resp_heic.json()["error"]["message"]
