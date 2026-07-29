"""Expenditure business rules, role boundaries, and transactions."""

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import Page, PaginationParams
from app.modules.auth.models import User, UserRole
from app.modules.expenditures.models import Expenditure
from app.modules.expenditures.repository import (
    add_expenditure,
    delete_expenditure,
    get_expenditure,
    list_expenditures,
)
from app.modules.expenditures.schemas import (
    ExpenditureCreate,
    ExpenditureResponse,
    ExpenditureUpdate,
)


def list_expenditures_for_user(
    db: Session,
    *,
    user: User,
    pagination: PaginationParams,
) -> Page[ExpenditureResponse]:
    """Return all family expenditures to an authenticated reader."""

    _require_reader(user)
    items, total = list_expenditures(db, offset=pagination.offset, limit=pagination.limit)
    return Page(
        items=[_to_response(expenditure) for expenditure in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


def get_expenditure_for_user_or_404(
    db: Session,
    *,
    user: User,
    expenditure_id: UUID,
) -> ExpenditureResponse:
    """Return one expenditure to an authenticated Family or Owner reader."""

    _require_reader(user)
    expenditure = get_expenditure(db, expenditure_id)
    if expenditure is None:
        raise _expenditure_not_found()
    return _to_response(expenditure)


def create_expenditure(
    db: Session,
    *,
    user: User,
    payload: ExpenditureCreate,
) -> ExpenditureResponse:
    """Create one exact Owner-recorded expenditure."""

    _require_owner(user)
    expenditure = Expenditure(
        created_by=user.id,
        creator=user,
        **payload.model_dump(),
    )
    add_expenditure(db, expenditure)
    _commit_and_refresh(db, expenditure)
    return _to_response(expenditure)


def update_expenditure(
    db: Session,
    *,
    user: User,
    expenditure_id: UUID,
    payload: ExpenditureUpdate,
) -> ExpenditureResponse:
    """Apply an Owner-controlled partial update to one expenditure."""

    _require_owner(user)
    expenditure = get_expenditure(db, expenditure_id)
    if expenditure is None:
        raise _expenditure_not_found()

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(expenditure, field_name, value)
    _commit_and_refresh(db, expenditure)
    return _to_response(expenditure)


def remove_expenditure(db: Session, *, user: User, expenditure_id: UUID) -> None:
    """Hard-delete one expenditure in an Owner-controlled transaction."""

    _require_owner(user)
    expenditure = get_expenditure(db, expenditure_id)
    if expenditure is None:
        raise _expenditure_not_found()
    delete_expenditure(db, expenditure)
    _commit(db)


def _to_response(expenditure: Expenditure) -> ExpenditureResponse:
    creator_display_name = getattr(expenditure.creator, "display_name", None)
    if not isinstance(creator_display_name, str):
        raise RuntimeError("Expenditure creator relationship is not loaded")
    return ExpenditureResponse(
        id=expenditure.id,
        created_by=expenditure.created_by,
        created_by_display_name=creator_display_name,
        spent_on=expenditure.spent_on,
        amount=expenditure.amount,
        currency=expenditure.currency,
        category=expenditure.category,
        description=expenditure.description,
        created_at=expenditure.created_at,
        updated_at=expenditure.updated_at,
    )


def _require_reader(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Expenditure access is not allowed",
        )


def _require_owner(user: User) -> None:
    if user.role is not UserRole.OWNER:
        raise AppError(status_code=403, code="FORBIDDEN", message="Owner access is required")


def _expenditure_not_found() -> AppError:
    return AppError(
        status_code=404,
        code="EXPENDITURE_NOT_FOUND",
        message="Expenditure was not found",
    )


def _commit_and_refresh(db: Session, expenditure: Expenditure) -> None:
    _commit(db)
    db.refresh(expenditure)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
