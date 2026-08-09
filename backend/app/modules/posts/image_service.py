"""Image storage, validation, processing, and access rules for Posts."""

from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.auth.models import User, UserRole
from app.modules.posts.models import Post, PostImage, PostImageStatus, PostVisibility

MAX_IMAGES = 9
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_LONG_EDGE = 4096
MAX_PIXELS = 16 * 1024 * 1024
MAX_TOTAL_SIZE = 30 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def upload_image(db: Session, *, user: User, upload: UploadFile) -> PostImage:
    """Validate one Family or Owner upload and persist a sanitized pending WebP."""

    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Family or Owner access is required",
        )
    data = upload.file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise AppError(status_code=400, code="IMAGE_TOO_LARGE", message="Image must be 5 MB or smaller")
    if not data:
        raise AppError(status_code=400, code="INVALID_IMAGE", message="Image file is empty")

    try:
        with Image.open(BytesIO(data)) as source:
            if source.format not in ALLOWED_FORMATS:
                raise ValueError("unsupported image format")
            source.load()
            width, height = source.size
            if max(width, height) > MAX_LONG_EDGE or width * height > MAX_PIXELS:
                raise ValueError("image dimensions exceed limits")
            has_alpha = source.mode in {"RGBA", "LA"} or (
                source.mode == "P" and "transparency" in source.info
            )
            processed = source.convert("RGBA" if has_alpha else "RGB")
            processed.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            output = BytesIO()
            processed.save(output, format="WEBP", quality=82, method=4)
            encoded = output.getvalue()
            processed_width, processed_height = processed.size
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE",
            message="The uploaded file is not a supported image",
        ) from error

    now = datetime.now(UTC)
    relative_path = Path("posts") / f"{now:%Y}" / f"{now:%m}" / f"{uuid4()}.webp"
    path = get_settings().media_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)

    image = PostImage(
        owner_id=user.id,
        storage_key=relative_path.as_posix(),
        mime_type="image/webp",
        file_size=len(encoded),
        width=processed_width,
        height=processed_height,
        status=PostImageStatus.PENDING,
    )
    db.add(image)
    try:
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return image


def attach_images(db: Session, *, user: User, post: Post, image_ids: list[UUID]) -> None:
    """Associate ordered pending uploads owned by the current Family or Owner user."""

    if len(image_ids) > MAX_IMAGES or len(set(image_ids)) != len(image_ids):
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE_LIST",
            message="A Post may contain at most 9 unique images",
        )
    if not image_ids:
        return
    images = list(
        db.scalars(
            select(PostImage).where(
                PostImage.id.in_(image_ids),
                PostImage.owner_id == user.id,
                PostImage.status == PostImageStatus.PENDING,
            )
        )
    )
    if len(images) != len(image_ids):
        raise AppError(
            status_code=400,
            code="INVALID_IMAGE_LIST",
            message="One or more images are unavailable",
        )
    by_id = {image.id: image for image in images}
    if sum(image.file_size for image in images) > MAX_TOTAL_SIZE:
        raise AppError(
            status_code=400,
            code="IMAGE_TOTAL_TOO_LARGE",
            message="Post images must total 30 MB or less",
        )
    for position, image_id in enumerate(image_ids):
        image = by_id[image_id]
        image.post = post
        image.position = position
        image.status = PostImageStatus.ATTACHED


def get_image_for_reader(db: Session, *, image_id: UUID, user: User | None) -> PostImage | None:
    """Return an attached image only when its Post is visible to the reader."""

    image = db.scalar(
        select(PostImage).where(
            PostImage.id == image_id,
            PostImage.status == PostImageStatus.ATTACHED,
        )
    )
    if image is None or image.post is None:
        return None
    if image.post.visibility is PostVisibility.PUBLIC:
        return image
    if user is not None and user.role in {UserRole.FAMILY, UserRole.OWNER}:
        return image
    return None


def image_path(image: PostImage) -> Path:
    """Resolve a database storage key without allowing traversal outside media root."""

    root = get_settings().media_root.resolve()
    path = (root / image.storage_key).resolve()
    if root not in path.parents:
        raise ValueError("Invalid image storage key")
    return path


def delete_detached_images(db: Session, images: list[PostImage]) -> None:
    """Remove detached files, retaining failed records for the cleanup command."""

    for image in images:
        try:
            image_path(image).unlink(missing_ok=True)
            db.delete(image)
        except OSError:
            image.status = PostImageStatus.CLEANUP_PENDING
    db.commit()


def cleanup_orphan_images(db: Session) -> int:
    """Delete pending uploads older than 24 hours and retry failed cleanups."""

    cutoff = datetime.now(UTC) - timedelta(hours=24)
    images = list(
        db.scalars(
            select(PostImage).where(
                (PostImage.status == PostImageStatus.CLEANUP_PENDING)
                | (
                    (PostImage.status == PostImageStatus.PENDING)
                    & (PostImage.created_at < cutoff)
                )
            )
        )
    )
    deleted = 0
    for image in images:
        try:
            image_path(image).unlink(missing_ok=True)
            db.delete(image)
            deleted += 1
        except OSError:
            image.status = PostImageStatus.CLEANUP_PENDING
    db.commit()
    return deleted
