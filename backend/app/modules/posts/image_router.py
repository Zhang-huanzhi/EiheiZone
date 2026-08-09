"""HTTP endpoints for Post image uploads and permission-checked reads."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
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
from app.modules.posts.image_service import get_image_for_reader, image_path, upload_image
from app.modules.posts.schemas import PostImageResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])
media_router = APIRouter(prefix="/media", tags=["media"])


@router.post("/image", response_model=PostImageResponse, status_code=status.HTTP_201_CREATED)
def upload_image_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> PostImageResponse:
    validate_csrf_request(request, current_user.session_id)
    image = upload_image(db, user=current_user.user, upload=file)
    return PostImageResponse.model_validate(image)


@media_router.get("/images/{image_id}")
def get_image_endpoint(
    image_id: UUID,
    current_user: CurrentUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> FileResponse:
    image = get_image_for_reader(
        db,
        image_id=image_id,
        user=current_user.user if current_user else None,
    )
    if image is None:
        raise AppError(status_code=404, code="IMAGE_NOT_FOUND", message="Image was not found")
    path = image_path(image)
    if not path.is_file():
        raise AppError(status_code=404, code="IMAGE_NOT_FOUND", message="Image was not found")
    cache_control = (
        "public, max-age=31536000, immutable"
        if image.post and image.post.visibility.value == "public"
        else "private, no-store"
    )
    return FileResponse(
        path,
        media_type=image.mime_type,
        headers={"Cache-Control": cache_control, "X-Content-Type-Options": "nosniff"},
    )
