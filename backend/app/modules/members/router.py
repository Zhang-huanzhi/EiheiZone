"""HTTP endpoints for Family Member Spaces, albums, story photos, and member media."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_optional,
    require_family_access,
    validate_csrf_request,
)
from app.modules.members.image_service import get_member_image_for_reader, get_or_create_member_image_thumbnail, member_image_path
from app.modules.members.schemas import (
    MemberAlbumCreate,
    MemberAlbumDetailResponse,
    MemberAlbumSummaryResponse,
    MemberAlbumUpdate,
    MemberImageResponse,
    MemberPhotoBatchCreate,
    MemberPhotoResponse,
    MemberPhotoUpdate,
    MemberProfileUpdate,
    MemberSpaceResponse,
    MemberSummaryCardResponse,
)
from app.modules.members.service import (
    add_photos_to_member_album,
    create_member_album,
    get_member_album_for_user_or_404,
    get_member_space_for_user_or_404,
    list_member_spaces_for_user,
    remove_member_album,
    remove_member_photo,
    remove_member_photo_direct,
    add_photos_to_member_gallery,
    update_member_album,
    update_member_photo,
    upload_image_for_member_space,
    upsert_member_profile,
)

router = APIRouter(prefix="/members", tags=["members"])
member_media_router = APIRouter(prefix="/media", tags=["media"])


@router.get("", response_model=list[MemberSummaryCardResponse])
def list_member_spaces_endpoint(
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> list[MemberSummaryCardResponse]:
    return list_member_spaces_for_user(db, user=current_user.user)


@router.get("/{user_id}", response_model=MemberSpaceResponse)
def get_member_space_endpoint(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberSpaceResponse:
    return get_member_space_for_user_or_404(db, user=current_user.user, target_user_id=user_id)


@router.put("/{user_id}/profile", response_model=MemberSpaceResponse)
def upsert_member_profile_endpoint(
    user_id: UUID,
    payload: MemberProfileUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberSpaceResponse:
    validate_csrf_request(request, current_user.session_id)
    return upsert_member_profile(
        db,
        user=current_user.user,
        target_user_id=user_id,
        payload=payload,
    )


@router.post(
    "/{user_id}/uploads/image",
    response_model=MemberImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_member_image_endpoint(
    user_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberImageResponse:
    validate_csrf_request(request, current_user.session_id)
    return upload_image_for_member_space(
        db,
        user=current_user.user,
        target_user_id=user_id,
        upload=file,
    )


@router.post(
    "/{user_id}/photos",
    response_model=list[MemberPhotoResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_member_gallery_photos_endpoint(
    user_id: UUID,
    payload: MemberPhotoBatchCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> list[MemberPhotoResponse]:
    validate_csrf_request(request, current_user.session_id)
    return add_photos_to_member_gallery(
        db,
        user=current_user.user,
        target_user_id=user_id,
        payload=payload,
    )


@router.delete(
    "/{user_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member_photo_direct_endpoint(
    user_id: UUID,
    photo_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    remove_member_photo_direct(
        db,
        user=current_user.user,
        target_user_id=user_id,
        photo_id=photo_id,
    )


@router.post(
    "/{user_id}/albums",
    response_model=MemberAlbumSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member_album_endpoint(
    user_id: UUID,
    payload: MemberAlbumCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberAlbumSummaryResponse:
    validate_csrf_request(request, current_user.session_id)
    return create_member_album(
        db,
        user=current_user.user,
        target_user_id=user_id,
        payload=payload,
    )


@router.get("/{user_id}/albums/{album_id}", response_model=MemberAlbumDetailResponse)
def get_member_album_endpoint(
    user_id: UUID,
    album_id: UUID,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberAlbumDetailResponse:
    return get_member_album_for_user_or_404(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
    )


@router.patch("/{user_id}/albums/{album_id}", response_model=MemberAlbumDetailResponse)
def update_member_album_endpoint(
    user_id: UUID,
    album_id: UUID,
    payload: MemberAlbumUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberAlbumDetailResponse:
    validate_csrf_request(request, current_user.session_id)
    return update_member_album(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
        payload=payload,
    )


@router.delete("/{user_id}/albums/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member_album_endpoint(
    user_id: UUID,
    album_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    remove_member_album(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
    )


@router.post(
    "/{user_id}/albums/{album_id}/photos",
    response_model=MemberAlbumDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member_photos_endpoint(
    user_id: UUID,
    album_id: UUID,
    payload: MemberPhotoBatchCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberAlbumDetailResponse:
    validate_csrf_request(request, current_user.session_id)
    return add_photos_to_member_album(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
        payload=payload,
    )


@router.patch(
    "/{user_id}/albums/{album_id}/photos/{photo_id}",
    response_model=MemberPhotoResponse,
)
def update_member_photo_endpoint(
    user_id: UUID,
    album_id: UUID,
    photo_id: UUID,
    payload: MemberPhotoUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> MemberPhotoResponse:
    validate_csrf_request(request, current_user.session_id)
    return update_member_photo(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
        photo_id=photo_id,
        payload=payload,
    )


@router.delete(
    "/{user_id}/albums/{album_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member_photo_endpoint(
    user_id: UUID,
    album_id: UUID,
    photo_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    remove_member_photo(
        db,
        user=current_user.user,
        target_user_id=user_id,
        album_id=album_id,
        photo_id=photo_id,
    )


@member_media_router.get("/member-images/{image_id}")
def get_member_image_endpoint(
    image_id: UUID,
    variant: Literal["full", "thumb"] = Query(default="full"),
    current_user: CurrentUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> FileResponse:
    image = get_member_image_for_reader(
        db,
        image_id=image_id,
        user=current_user.user if current_user else None,
    )
    if image is None:
        raise AppError(status_code=404, code="IMAGE_NOT_FOUND", message="Image was not found")
    if variant == "thumb":
        path = get_or_create_member_image_thumbnail(image)
    else:
        path = member_image_path(image)
    if not path.is_file():
        raise AppError(status_code=404, code="IMAGE_NOT_FOUND", message="Image was not found")
    return FileResponse(
        path,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
