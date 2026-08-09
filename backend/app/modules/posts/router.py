"""HTTP endpoints for public and authenticated Post access."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, Pagination
from app.db.session import get_db
from app.modules.auth.dependencies import CurrentUser, require_family_access, require_owner, validate_csrf_request
from app.modules.posts.schemas import PostCreate, PostResponse, PostUpdate
from app.modules.posts.service import (
    create_post,
    get_post_for_user_or_404,
    get_public_post_or_404,
    list_posts_for_user,
    list_public_posts_page,
    remove_post,
    update_post,
)


public_router = APIRouter(prefix="/public/posts", tags=["public-posts"])
router = APIRouter(prefix="/posts", tags=["posts"])


@public_router.get("", response_model=Page[PostResponse])
def list_public_posts(pagination: Pagination, db: Session = Depends(get_db)) -> Page[PostResponse]:
    return list_public_posts_page(db, pagination)


@public_router.get("/{post_id}", response_model=PostResponse)
def get_public_post(post_id: UUID, db: Session = Depends(get_db)) -> PostResponse:
    return get_public_post_or_404(db, post_id)


@router.get("", response_model=Page[PostResponse])
def list_posts(
    pagination: Pagination,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> Page[PostResponse]:
    return list_posts_for_user(db, user=current_user.user, pagination=pagination)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: UUID,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> PostResponse:
    return get_post_for_user_or_404(db, user=current_user.user, post_id=post_id)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post_endpoint(
    payload: PostCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> PostResponse:
    validate_csrf_request(request, current_user.session_id)
    return create_post(db, user=current_user.user, payload=payload)


@router.patch("/{post_id}", response_model=PostResponse)
def update_post_endpoint(
    post_id: UUID,
    payload: PostUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> PostResponse:
    validate_csrf_request(request, current_user.session_id)
    return update_post(db, user=current_user.user, post_id=post_id, payload=payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_endpoint(
    post_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    remove_post(db, user=current_user.user, post_id=post_id)
