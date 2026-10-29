"""Image storage, validation, processing, and access rules for Posts."""

from dataclasses import asdict, dataclass
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
from app.modules.notifications.service import enqueue_media_cleanup_failure
from app.modules.posts.models import MediaCleanupRun, Post, PostImage, PostImageStatus, PostVisibility

MAX_IMAGES = 9
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_LONG_EDGE = 4096
MAX_PIXELS = 16 * 1024 * 1024
MAX_TOTAL_SIZE = 30 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ORPHAN_GRACE = timedelta(hours=24)


@dataclass
class CleanupStats:
    scanned_files: int = 0
    pending_candidates: int = 0
    orphan_candidates: int = 0
    files_deleted: int = 0
    records_deleted: int = 0
    retry_count: int = 0
    failed_count: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


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


def replace_post_images(
    db: Session,
    *,
    user: User,
    post: Post,
    image_ids: list[UUID],
) -> list[PostImage]:
    """Replace a Post's ordered image list and return detached images for cleanup."""

    if len(image_ids) > MAX_IMAGES or len(set(image_ids)) != len(image_ids):
        raise AppError(status_code=400, code="INVALID_IMAGE_LIST", message="A Post may contain at most 9 unique images")
    current = {image.id: image for image in post.images if image.status is PostImageStatus.ATTACHED}
    if not image_ids and not current:
        return []
    requested = list(
        db.scalars(
            select(PostImage).where(
                PostImage.id.in_(image_ids),
                (PostImage.status == PostImageStatus.PENDING)
                | ((PostImage.status == PostImageStatus.ATTACHED) & (PostImage.post_id == post.id)),
            )
        )
    ) if image_ids else []
    if len(requested) != len(image_ids):
        raise AppError(status_code=400, code="INVALID_IMAGE_LIST", message="One or more images are unavailable")
    by_id = {image.id: image for image in requested}
    for image in requested:
        if image.status is PostImageStatus.PENDING and image.owner_id != user.id:
            raise AppError(status_code=400, code="INVALID_IMAGE_LIST", message="One or more images are unavailable")
    if sum(image.file_size for image in requested) > MAX_TOTAL_SIZE:
        raise AppError(status_code=400, code="IMAGE_TOTAL_TOO_LARGE", message="Post images must total 30 MB or less")
    detached = [image for image_id, image in current.items() if image_id not in by_id]
    for image in detached:
        image.post = None
        image.status = PostImageStatus.CLEANUP_PENDING
    for position, image_id in enumerate(image_ids):
        image = by_id[image_id]
        image.post = post
        image.position = position
        image.status = PostImageStatus.ATTACHED
    return detached


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
            image.cleanup_attempts += 1
            image.last_cleanup_at = datetime.now(UTC)
            image.last_cleanup_error = "physical file deletion failed"
    db.commit()


def cleanup_orphan_images(
    db: Session,
    *,
    dry_run: bool = False,
    scan_orphans: bool = False,
    max_items: int | None = None,
    grace_period: timedelta = ORPHAN_GRACE,
) -> CleanupStats:
    """Clean stale database records and unreferenced media files with statistics."""

    if max_items is not None and max_items <= 0:
        raise ValueError("max_items must be positive")
    now = datetime.now(UTC)
    cutoff = now - grace_period
    stats = CleanupStats()
    images = list(
        db.scalars(
            select(PostImage).where(
                (PostImage.status == PostImageStatus.CLEANUP_PENDING)
                | ((PostImage.status == PostImageStatus.PENDING) & (PostImage.created_at < cutoff))
            ).order_by(PostImage.created_at)
        )
    )
    stats.pending_candidates = len(images)
    known_keys = set(db.scalars(select(PostImage.storage_key)))
    files: list[Path] = []
    root = get_settings().media_root
    if scan_orphans and root.exists():
        files = [path for path in root.rglob("*") if path.is_file() and path.stat().st_mtime < cutoff.timestamp()]
        stats.scanned_files = len(files)
        files = [path for path in files if path.is_relative_to(root.resolve()) and path.relative_to(root).as_posix() not in known_keys]
        stats.orphan_candidates = len(files)
    candidates = [("image", image) for image in images] + [("file", path) for path in files]
    if max_items is not None:
        candidates = candidates[:max_items]
    for kind, candidate in candidates:
        if kind == "image":
            image = candidate
            if dry_run:
                continue
            try:
                image_path(image).unlink(missing_ok=True)
                db.delete(image)
                stats.files_deleted += 1
                stats.records_deleted += 1
                if image.cleanup_attempts:
                    stats.retry_count += 1
            except OSError as error:
                image.status = PostImageStatus.CLEANUP_PENDING
                image.cleanup_attempts += 1
                image.last_cleanup_at = now
                image.last_cleanup_error = str(error)[:500]
                stats.failed_count += 1
        else:
            path = candidate
            if dry_run:
                continue
            try:
                path.unlink()
                stats.files_deleted += 1
            except OSError:
                stats.failed_count += 1
    if not dry_run:
        db.commit()
    return stats


def run_media_cleanup(
    db: Session,
    *,
    dry_run: bool = False,
    scan_orphans: bool = True,
    max_items: int | None = None,
) -> tuple[MediaCleanupRun | None, CleanupStats]:
    """Run cleanup, persist an operational record, and enqueue Owner alerts on failure."""

    if dry_run:
        return None, cleanup_orphan_images(db, dry_run=True, scan_orphans=scan_orphans, max_items=max_items)
    run = MediaCleanupRun(dry_run=False, scan_orphans=scan_orphans)
    db.add(run)
    db.commit()
    try:
        stats = cleanup_orphan_images(db, scan_orphans=scan_orphans, max_items=max_items)
        run.finished_at = datetime.now(UTC)
        run.status = "failed" if stats.failed_count else "succeeded"
        run.pending_candidates = stats.pending_candidates
        run.orphan_candidates = stats.orphan_candidates
        run.files_deleted = stats.files_deleted
        run.records_deleted = stats.records_deleted
        run.retry_count = stats.retry_count
        run.failed_count = stats.failed_count
        if stats.failed_count:
            run.error_summary = f"{stats.failed_count} media cleanup item(s) failed"
            enqueue_media_cleanup_failure(db, run_id=run.id, summary=run.error_summary)
        db.commit()
    except Exception as error:
        db.rollback()
        run = db.get(MediaCleanupRun, run.id) or run
        run.finished_at = datetime.now(UTC)
        run.status = "failed"
        run.error_summary = str(error)[:1000]
        db.add(run)
        enqueue_media_cleanup_failure(db, run_id=run.id, summary=run.error_summary)
        db.commit()
        raise
    return run, stats
