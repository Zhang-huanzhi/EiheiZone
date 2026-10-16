from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import PaginationParams
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.posts.models import PostComment
from app.modules.posts.schemas import PostCommentCreate, PostCreate
from app.modules.posts.service import (
    create_post,
    create_post_comment,
    list_post_comments_for_user,
    remove_post,
    remove_post_comment,
)


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole, suffix: str = ""):
    return create_user(
        test_session,
        login_name=f"post-comment-{role.value}-{suffix or uuid4().hex}",
        display_name=f"{role.value.title()} Comment User",
        role=role,
        plain_password=PASSWORD,
    )


def test_comment_schema_rejects_blank_and_oversized_body() -> None:
    for body in ("", "   ", "x" * 2001):
        with pytest.raises(ValidationError):
            PostCommentCreate(body=body)


def test_comment_service_lists_newest_first_and_enforces_delete_permissions(
    test_session: Session,
) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    family = create_account(test_session, UserRole.FAMILY, "family")
    other_family = create_account(test_session, UserRole.FAMILY, "other")
    post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Comment target", body="Post body"),
    )

    first = create_post_comment(
        test_session,
        user=family,
        post_id=post.id,
        payload=PostCommentCreate(body="First comment"),
    )
    second = create_post_comment(
        test_session,
        user=owner,
        post_id=post.id,
        payload=PostCommentCreate(body="Second comment"),
    )

    page = list_post_comments_for_user(
        test_session,
        user=family,
        post_id=post.id,
        pagination=PaginationParams(),
    )
    assert [item.id for item in page.items] == [second.id, first.id]
    assert page.total == 2
    assert page.items[0].author_display_name == owner.display_name

    with pytest.raises(AppError) as forbidden:
        remove_post_comment(
            test_session,
            user=other_family,
            post_id=post.id,
            comment_id=first.id,
        )
    assert forbidden.value.status_code == 403

    remove_post_comment(
        test_session,
        user=family,
        post_id=post.id,
        comment_id=first.id,
    )
    assert test_session.get(PostComment, first.id) is None

    remove_post_comment(
        test_session,
        user=owner,
        post_id=post.id,
        comment_id=second.id,
    )
    assert test_session.get(PostComment, second.id) is None


def test_delete_post_cascades_comments(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Cascade target", body="Post body"),
    )
    comment = create_post_comment(
        test_session,
        user=owner,
        post_id=post.id,
        payload=PostCommentCreate(body="Will be removed"),
    )

    remove_post(test_session, user=owner, post_id=post.id)

    assert test_session.get(PostComment, comment.id) is None
