from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import PaginationParams
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.posts.models import PostVisibility
from app.modules.posts.schemas import PostCreate, PostUpdate
from app.modules.posts.service import (
    create_post,
    get_post_for_user_or_404,
    get_public_post_or_404,
    list_posts_for_user,
    list_public_posts_page,
    remove_post,
    update_post,
)


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole):
    return create_user(
        test_session,
        login_name=f"post-service-{role.value}-{uuid4().hex}",
        display_name=f"{role.value.title()} User",
        role=role,
        plain_password=PASSWORD,
    )


def test_post_services_enforce_visibility_and_owner_writes(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    family = create_account(test_session, UserRole.FAMILY)
    family_post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Family update", body="Family body"),
    )
    public_post = create_post(
        test_session,
        user=owner,
        payload=PostCreate(
            title="Public update",
            body="Public body",
            visibility=PostVisibility.PUBLIC,
        ),
    )

    public_page = list_public_posts_page(test_session, PaginationParams())
    family_page = list_posts_for_user(test_session, user=family, pagination=PaginationParams())

    assert [post.id for post in public_page.items] == [public_post.id]
    assert {post.id for post in family_page.items} == {public_post.id, family_post.id}
    assert get_post_for_user_or_404(test_session, user=family, post_id=family_post.id).id == family_post.id
    with pytest.raises(AppError, match="Post was not found"):
        get_public_post_or_404(test_session, family_post.id)
    with pytest.raises(AppError) as error:
        create_post(
            test_session,
            user=family,
            payload=PostCreate(title="Forbidden", body="Forbidden body"),
        )
    assert error.value.status_code == 403


def test_post_service_patches_only_supplied_fields_and_hard_deletes(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    created = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Before", body="Original body"),
    )

    updated = update_post(
        test_session,
        user=owner,
        post_id=created.id,
        payload=PostUpdate(title="After"),
    )

    assert updated.title == "After"
    assert updated.body == "Original body"
    remove_post(test_session, user=owner, post_id=created.id)
    with pytest.raises(AppError) as error:
        get_post_for_user_or_404(test_session, user=owner, post_id=created.id)
    assert error.value.status_code == 404


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
def test_post_write_services_roll_back_when_commit_fails(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    created = create_post(
        test_session,
        user=owner,
        payload=PostCreate(title="Rollback target", body="Rollback body"),
    )
    rollback_calls = 0
    original_rollback = test_session.rollback

    def fail_commit() -> None:
        raise OperationalError("COMMIT", {}, None)

    def record_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback()

    monkeypatch.setattr(test_session, "commit", fail_commit)
    monkeypatch.setattr(test_session, "rollback", record_rollback)

    with pytest.raises(OperationalError):
        if operation == "create":
            create_post(
                test_session,
                user=owner,
                payload=PostCreate(title="New post", body="New body"),
            )
        elif operation == "update":
            update_post(
                test_session,
                user=owner,
                post_id=created.id,
                payload=PostUpdate(title="Failed update"),
            )
        else:
            remove_post(test_session, user=owner, post_id=created.id)

    assert rollback_calls == 1
