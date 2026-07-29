"""HTTP endpoints for authenticated Expenditure reading and Owner management."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, Pagination
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    require_family_access,
    require_owner,
    validate_csrf_request,
)
from app.modules.expenditures.schemas import (
    ExpenditureCreate,
    ExpenditureResponse,
    ExpenditureUpdate,
)
from app.modules.expenditures.service import (
    create_expenditure,
    get_expenditure_for_user_or_404,
    list_expenditures_for_user,
    remove_expenditure,
    update_expenditure,
)


router = APIRouter(prefix="/expenditures", tags=["expenditures"])


@router.get("", response_model=Page[ExpenditureResponse])
def list_expenditure_records(
    pagination: Pagination,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> Page[ExpenditureResponse]:
    return list_expenditures_for_user(db, user=current_user.user, pagination=pagination)


@router.get("/{expenditure_id}", response_model=ExpenditureResponse)
def get_expenditure_record(
    expenditure_id: UUID,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> ExpenditureResponse:
    return get_expenditure_for_user_or_404(
        db,
        user=current_user.user,
        expenditure_id=expenditure_id,
    )


@router.post("", response_model=ExpenditureResponse, status_code=status.HTTP_201_CREATED)
def create_expenditure_endpoint(
    payload: ExpenditureCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> ExpenditureResponse:
    validate_csrf_request(request, current_user.session_id)
    return create_expenditure(db, user=current_user.user, payload=payload)


@router.patch("/{expenditure_id}", response_model=ExpenditureResponse)
def update_expenditure_endpoint(
    expenditure_id: UUID,
    payload: ExpenditureUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> ExpenditureResponse:
    validate_csrf_request(request, current_user.session_id)
    return update_expenditure(
        db,
        user=current_user.user,
        expenditure_id=expenditure_id,
        payload=payload,
    )


@router.delete("/{expenditure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expenditure_endpoint(
    expenditure_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    remove_expenditure(db, user=current_user.user, expenditure_id=expenditure_id)
