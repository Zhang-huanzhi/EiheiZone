"""Post business rules, visibility boundaries, and transactions."""

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import Page, PaginationParams
from app.modules.auth.models import User, UserRole
from app.modules.posts.models import Post, PostImageStatus
from app.modules.posts.image_service import attach_images, delete_detached_images
from app.modules.posts.repository import (
    add_post,
    delete_post,
    get_public_post,
    get_visible_post,
    list_public_posts,
    list_visible_posts,
)
from app.modules.posts.schemas import PostCreate, PostResponse, PostUpdate


def list_public_posts_page(db: Session, pagination: PaginationParams) -> Page[PostResponse]:
    """Return the public-only Post page."""

    items, total = list_public_posts(db, offset=pagination.offset, limit=pagination.limit)
    return _page(items, total, pagination)


def get_public_post_or_404(db: Session, post_id: UUID) -> PostResponse:
    """Return one public Post, hiding family-only records as not found."""

    post = get_public_post(db, post_id)
    if post is None:
        raise _post_not_found()
    return _to_response(post)


def list_posts_for_user(
    db: Session,
    *,
    user: User,
    pagination: PaginationParams,
) -> Page[PostResponse]:
    """Return all Post visibility levels for a valid Family or Owner user."""

    _require_reader(user)
    items, total = list_visible_posts(db, offset=pagination.offset, limit=pagination.limit)
    return _page(items, total, pagination)


def get_post_for_user_or_404(db: Session, *, user: User, post_id: UUID) -> PostResponse:
    """Return one Post for a valid Family or Owner user."""

    _require_reader(user)
    post = get_visible_post(db, post_id)
    if post is None:
        raise _post_not_found()
    return _to_response(post)


def create_post(db: Session, *, user: User, payload: PostCreate) -> PostResponse:
    """Create one Post in a Family or Owner-controlled transaction."""

    _require_writer(user)
    post_data = payload.model_dump(exclude={"image_ids"})
    post = Post(author_id=user.id, author=user, **post_data)
    add_post(db, post)
    attach_images(db, user=user, post=post, image_ids=payload.image_ids)
    _commit_and_refresh(db, post)
    return _to_response(post)


def update_post(
    db: Session,
    *,
    user: User,
    post_id: UUID,
    payload: PostUpdate,
) -> PostResponse:
    """Apply a non-empty Owner patch to one Post."""

    _require_owner(user)
    post = get_visible_post(db, post_id)
    if post is None:
        raise _post_not_found()

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field_name, value)
    _commit_and_refresh(db, post)
    return _to_response(post)


def remove_post(db: Session, *, user: User, post_id: UUID) -> None:
    """Hard-delete one Post in an Owner-controlled transaction."""

    _require_owner(user)
    post = get_visible_post(db, post_id)
    if post is None:
        raise _post_not_found()
    images = list(post.images)
    for image in images:
        image.post = None
        image.status = PostImageStatus.CLEANUP_PENDING
    delete_post(db, post)
    _commit(db)
    delete_detached_images(db, images)


def _page(items: list[Post], total: int, pagination: PaginationParams) -> Page[PostResponse]:
    return Page(
        items=[_to_response(post) for post in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


def _require_reader(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(status_code=403, code="FORBIDDEN", message="Post access is not allowed")


def _require_owner(user: User) -> None:
    if user.role is not UserRole.OWNER:
        raise AppError(status_code=403, code="FORBIDDEN", message="Owner access is required")


def _require_writer(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Family or Owner access is required",
        )


def _to_response(post: Post) -> PostResponse:
    author_display_name = getattr(post.author, "display_name", None)
    if not isinstance(author_display_name, str):
        raise RuntimeError("Post author relationship is not loaded")
    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_display_name=author_display_name,
        title=post.title,
        body=post.body,
        visibility=post.visibility,
        created_at=post.created_at,
        updated_at=post.updated_at,
        images=post.images,
    )


def _post_not_found() -> AppError:
    return AppError(status_code=404, code="POST_NOT_FOUND", message="Post was not found")


def _commit_and_refresh(db: Session, post: Post) -> None:
    _commit(db)
    db.refresh(post)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
