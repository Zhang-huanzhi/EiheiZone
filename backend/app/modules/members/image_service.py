"""Image storage, validation, EXIF orientation normalization, and access rules for Member Spaces."""

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.auth.models import User, UserRole
from app.modules.members.models import (
    MemberAlbum,
    MemberImage,
    MemberImageStatus,
    MemberPhoto,
    MemberProfile,
)

MAX_BATCH_PHOTOS = 300
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_LONG_EDGE = 16384
MAX_PIXELS = 75 * 1024 * 1024
MAX_TOTAL_SIZE = 500 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP", "AVIF", "GIF", "BMP", "DIB", "TIFF"}
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"}
THUMBNAIL_MAX_EDGE = 480
THUMBNAIL_QUALITY = 78


def _is_heic_header(data: bytes) -> bool:
    """Detect ISO Base Media File Format headers used by Apple HEIC/HEIF photos."""

    return len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12].lower() in _HEIC_BRANDS


def upload_member_image(
    db: Session,
    *,
    actor: User,
    target_user: User,
    upload: UploadFile,
) -> MemberImage:
    """Validate one upload for a member space and persist an orientation-corrected pending WebP."""

    if actor.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Family or Owner access is required",
        )
    if actor.role is not UserRole.OWNER and actor.id != target_user.id:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="You may only upload images to your own member space",
        )

    data = upload.file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise AppError(
            status_code=400,
            code="IMAGE_TOO_LARGE",
            message="单张图片大小不能超过 20 MB。",
        )
    if not data:
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="图片文件为空，请重新选择。",
        )
    if _is_heic_header(data):
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="检测到苹果 HEIC 原图格式，请先在系统相册中导出为 JPG/PNG 后再上传。",
        )

    try:
        with Image.open(BytesIO(data)) as source:
            fmt = (source.format or "").upper()
            if fmt not in ALLOWED_FORMATS:
                raise AppError(
                    status_code=400,
                    code="INVALID_IMAGE",
                    message=f"不支持该图片格式（{fmt or '未知'}），请选择 JPG、PNG、WebP、AVIF、GIF 或 BMP 图片。",
                )
            width, height = source.size
            if max(width, height) > MAX_LONG_EDGE or width * height > MAX_PIXELS:
                raise AppError(
                    status_code=400,
                    code="INVALID_IMAGE",
                    message=f"图片分辨率过高（当前 {width}×{height}，最高支持约 7500 万像素），请适当裁剪后重试。",
                )
            source.load()
            transposed = ImageOps.exif_transpose(source)
            has_alpha = transposed.mode in {"RGBA", "LA"} or (
                transposed.mode == "P" and "transparency" in transposed.info
            )
            processed = transposed.convert("RGBA" if has_alpha else "RGB")
            processed.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            output = BytesIO()
            processed.save(output, format="WEBP", quality=82, method=4)
            encoded = output.getvalue()
            processed_width, processed_height = processed.size
            thumb_image = processed.copy()
            thumb_image.thumbnail((THUMBNAIL_MAX_EDGE, THUMBNAIL_MAX_EDGE), Image.Resampling.LANCZOS)
            thumb_output = BytesIO()
            thumb_image.save(thumb_output, format="WEBP", quality=THUMBNAIL_QUALITY, method=4)
            thumb_encoded = thumb_output.getvalue()
    except AppError:
        raise
    except Image.DecompressionBombError as error:
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="图片分辨率过高（超过安全上限），请适当裁剪后重试。",
        ) from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="图片文件已损坏或格式不受支持，请选择 JPG、PNG 或 WebP 图片重试。",
        ) from error

    now = datetime.now(UTC)
    relative_path = Path("members") / f"{now:%Y}" / f"{now:%m}" / f"{uuid4()}.webp"
    path = get_settings().media_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    thumb_path = path.with_name(f"{path.stem}_thumb.webp")
    thumb_path.write_bytes(thumb_encoded)

    image = MemberImage(
        owner_id=actor.id,
        target_user_id=target_user.id,
        storage_key=relative_path.as_posix(),
        mime_type="image/webp",
        file_size=len(encoded),
        width=processed_width,
        height=processed_height,
        status=MemberImageStatus.PENDING,
    )
    db.add(image)
    try:
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        thumb_path.unlink(missing_ok=True)
        raise
    return image


def resolve_slot_image(
    db: Session,
    *,
    target_user_id: UUID,
    current_image: MemberImage | None,
    requested_image_id: UUID | None,
    allow_attached_for_user: bool = False,
) -> tuple[MemberImage | None, MemberImage | None]:
    """Resolve a profile avatar/banner or album cover slot and return (new_image, old_image)."""

    if requested_image_id is None:
        return None, current_image
    if current_image is not None and current_image.id == requested_image_id:
        return current_image, None

    allowed_statuses = {MemberImageStatus.PENDING}
    if allow_attached_for_user:
        allowed_statuses.add(MemberImageStatus.ATTACHED)

    candidate = db.scalar(
        select(MemberImage).where(
            MemberImage.id == requested_image_id,
            MemberImage.target_user_id == target_user_id,
            MemberImage.status.in_(allowed_statuses),
        )
    )
    if candidate is None:
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="The requested member image is unavailable",
        )
    candidate.status = MemberImageStatus.ATTACHED
    return candidate, current_image


def attach_batch_album_images(
    db: Session,
    *,
    target_user_id: UUID,
    image_ids: list[UUID],
) -> dict[UUID, MemberImage]:
    """Validate and attach 1..9 pending member images for an album photo batch."""

    if not image_ids or len(image_ids) > MAX_BATCH_PHOTOS or len(set(image_ids)) != len(image_ids):
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE_LIST",
            message=f"单次批量上传照片数量需在 1 至 {MAX_BATCH_PHOTOS} 张之间，且不能重复",
        )
    images = list(
        db.scalars(
            select(MemberImage).where(
                MemberImage.id.in_(image_ids),
                MemberImage.target_user_id == target_user_id,
                MemberImage.status == MemberImageStatus.PENDING,
            )
        )
    )
    if len(images) != len(image_ids):
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE_LIST",
            message="部分待关联照片不存在或已被处理",
        )
    if sum(image.file_size for image in images) > MAX_TOTAL_SIZE:
        raise AppError(
            status_code=400,
            code="IMAGE_TOTAL_TOO_LARGE",
            message="单次批量保存的照片总大小超出上限",
        )
    by_id: dict[UUID, MemberImage] = {}
    for image in images:
        image.status = MemberImageStatus.ATTACHED
        by_id[image.id] = image
    return by_id


def is_member_image_referenced(db: Session, image_id: UUID) -> bool:
    """Return True when the image is still used by any profile, album cover, or photo."""

    db.flush()
    profile_refs = db.scalar(
        select(func.count())
        .select_from(MemberProfile)
        .where(
            (MemberProfile.avatar_image_id == image_id)
            | (MemberProfile.banner_image_id == image_id)
        )
    )
    if profile_refs:
        return True
    album_refs = db.scalar(
        select(func.count())
        .select_from(MemberAlbum)
        .where(MemberAlbum.cover_image_id == image_id)
    )
    if album_refs:
        return True
    photo_refs = db.scalar(
        select(func.count())
        .select_from(MemberPhoto)
        .where(MemberPhoto.image_id == image_id)
    )
    return bool(photo_refs)


def stage_unreferenced_member_images_for_cleanup(
    db: Session,
    candidates: list[MemberImage],
) -> list[MemberImage]:
    """Mark candidate images that have no remaining database references as CLEANUP_PENDING."""

    seen: set[UUID] = set()
    detached: list[MemberImage] = []
    for image in candidates:
        if image.id in seen:
            continue
        seen.add(image.id)
        if not is_member_image_referenced(db, image.id):
            image.status = MemberImageStatus.CLEANUP_PENDING
            detached.append(image)
    return detached


def member_image_path(image: MemberImage) -> Path:
    """Resolve a database storage key without allowing traversal outside media root."""

    root = get_settings().media_root.resolve()
    path = (root / image.storage_key).resolve()
    if root not in path.parents:
        raise ValueError("Invalid member image storage key")
    return path


def member_image_thumbnail_path(image: MemberImage) -> Path:
    """Resolve the companion thumbnail file path for a member image."""

    full_path = member_image_path(image)
    return full_path.with_name(f"{full_path.stem}_thumb.webp")


def get_or_create_member_image_thumbnail(image: MemberImage) -> Path:
    """Return the companion thumbnail path, generating and saving it on disk if absent."""

    thumb_path = member_image_thumbnail_path(image)
    if thumb_path.is_file():
        return thumb_path

    full_path = member_image_path(image)
    if not full_path.is_file():
        raise AppError(status_code=404, code="IMAGE_NOT_FOUND", message="Image was not found")

    try:
        with Image.open(full_path) as source:
            has_alpha = source.mode in {"RGBA", "LA"} or (
                source.mode == "P" and "transparency" in source.info
            )
            processed = source.convert("RGBA" if has_alpha else "RGB")
            processed.thumbnail((THUMBNAIL_MAX_EDGE, THUMBNAIL_MAX_EDGE), Image.Resampling.LANCZOS)
            output = BytesIO()
            processed.save(output, format="WEBP", quality=THUMBNAIL_QUALITY, method=4)
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            thumb_path.write_bytes(output.getvalue())
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise AppError(
            status_code=500,
            code="THUMBNAIL_GENERATION_FAILED",
            message="Failed to generate thumbnail for member image",
        ) from error

    return thumb_path


def delete_detached_member_images(db: Session, images: list[MemberImage]) -> None:
    """Remove detached member image files, retaining failed records for worker retry."""

    if not images:
        return
    for image in images:
        try:
            member_image_path(image).unlink(missing_ok=True)
            member_image_thumbnail_path(image).unlink(missing_ok=True)
            db.delete(image)
        except OSError:
            image.status = MemberImageStatus.CLEANUP_PENDING
            image.cleanup_attempts += 1
            image.last_cleanup_at = datetime.now(UTC)
            image.last_cleanup_error = "physical file deletion failed"
    db.commit()


def get_member_image_for_reader(
    db: Session,
    *,
    image_id: UUID,
    user: User | None,
) -> MemberImage | None:
    """Return a member image only for an authenticated Family or Owner reader."""

    if user is None or user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        return None
    image = db.scalar(select(MemberImage).where(MemberImage.id == image_id))
    if image is None:
        return None
    if image.status is MemberImageStatus.ATTACHED:
        return image
    if image.status is MemberImageStatus.PENDING and (
        user.role is UserRole.OWNER
        or image.owner_id == user.id
        or image.target_user_id == user.id
    ):
        return image
    return None
