"""Database access helpers for Post records."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.posts.models import Post, PostVisibility


def list_public_posts(db: Session, *, offset: int, limit: int) -> tuple[list[Post], int]:
    """Return only publicly visible posts and the matching total."""

    statement = _ordered_posts().where(Post.visibility == PostVisibility.PUBLIC)
    return _list_and_count(db, statement, offset=offset, limit=limit)


def get_public_post(db: Session, post_id: UUID) -> Post | None:
    """Return one public post without revealing family-only records."""

    statement = select(Post).where(
        Post.id == post_id,
        Post.visibility == PostVisibility.PUBLIC,
    )
    return db.scalar(statement)


def list_visible_posts(db: Session, *, offset: int, limit: int) -> tuple[list[Post], int]:
    """Return all posts for an already authenticated Family or Owner reader."""

    return _list_and_count(db, _ordered_posts(), offset=offset, limit=limit)


def get_visible_post(db: Session, post_id: UUID) -> Post | None:
    """Return one post for an already authenticated Family or Owner reader."""

    return db.get(Post, post_id)


def add_post(db: Session, post: Post) -> None:
    """Stage a new post for the surrounding service transaction."""

    db.add(post)


def delete_post(db: Session, post: Post) -> None:
    """Stage a hard deletion without committing it."""

    db.delete(post)


def _ordered_posts():
    return select(Post).order_by(Post.created_at.desc(), Post.id.desc())


def _list_and_count(
    db: Session,
    statement,
    *,
    offset: int,
    limit: int,
) -> tuple[list[Post], int]:
    items = list(db.scalars(statement.offset(offset).limit(limit)))
    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = db.scalar(count_statement)
    return items, int(total or 0)
