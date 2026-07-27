from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.posts.models import Post, PostVisibility
from app.modules.posts.repository import (
    add_post,
    delete_post,
    get_public_post,
    get_visible_post,
    list_public_posts,
    list_visible_posts,
)


PASSWORD = "test-password-123"


def create_owner(test_session: Session):
    return create_user(
        test_session,
        login_name=f"post-repository-owner-{uuid4().hex}",
        display_name="Repository Owner",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )


def make_post(owner_id, *, title: str, visibility: PostVisibility, created_at: datetime) -> Post:
    return Post(
        author_id=owner_id,
        title=title,
        body=f"Body for {title}",
        visibility=visibility,
        created_at=created_at,
        updated_at=created_at,
    )


def test_public_repository_filters_family_posts_and_orders_results(test_session: Session) -> None:
    owner = create_owner(test_session)
    now = datetime.now(UTC)
    public_old = make_post(
        owner.id,
        title="Public old",
        visibility=PostVisibility.PUBLIC,
        created_at=now - timedelta(minutes=2),
    )
    family_new = make_post(
        owner.id,
        title="Family new",
        visibility=PostVisibility.FAMILY,
        created_at=now,
    )
    public_new = make_post(
        owner.id,
        title="Public new",
        visibility=PostVisibility.PUBLIC,
        created_at=now - timedelta(minutes=1),
    )
    test_session.add_all([public_old, family_new, public_new])
    test_session.flush()

    items, total = list_public_posts(test_session, offset=0, limit=20)

    assert [post.id for post in items] == [public_new.id, public_old.id]
    assert total == 2
    assert get_public_post(test_session, family_new.id) is None
    assert get_visible_post(test_session, family_new.id) == family_new


def test_visible_repository_paginates_all_visibility_levels(test_session: Session) -> None:
    owner = create_owner(test_session)
    now = datetime.now(UTC)
    posts = [
        make_post(
            owner.id,
            title=f"Post {index}",
            visibility=PostVisibility.PUBLIC if index % 2 else PostVisibility.FAMILY,
            created_at=now - timedelta(minutes=index),
        )
        for index in range(3)
    ]
    test_session.add_all(posts)
    test_session.flush()

    items, total = list_visible_posts(test_session, offset=1, limit=1)

    assert total == 3
    assert len(items) == 1
    assert items[0].title == "Post 1"


def test_add_and_delete_post_leave_commit_to_service(test_session: Session) -> None:
    owner = create_owner(test_session)
    post = Post(author_id=owner.id, title="Staged", body="Staged body")

    add_post(test_session, post)
    test_session.flush()
    assert test_session.get(Post, post.id) == post

    delete_post(test_session, post)
    test_session.flush()
    assert test_session.get(Post, post.id) is None
