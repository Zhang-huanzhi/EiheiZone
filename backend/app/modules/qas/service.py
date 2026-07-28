"""QA business rules, role boundaries, state consistency, and transactions."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import Page, PaginationParams
from app.modules.auth.models import User, UserRole
from app.modules.qas.models import QA, QAStatus
from app.modules.qas.repository import add_qa, get_qa, list_qas
from app.modules.qas.schemas import QACreate, QAAnswerUpsert, QAResponse


def list_qas_for_user(
    db: Session,
    *,
    user: User,
    pagination: PaginationParams,
) -> Page[QAResponse]:
    """Return all family QAs to an authenticated Family or Owner reader."""

    _require_reader(user)
    items, total = list_qas(db, offset=pagination.offset, limit=pagination.limit)
    return Page(
        items=[_to_response(qa) for qa in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


def get_qa_for_user_or_404(db: Session, *, user: User, qa_id: UUID) -> QAResponse:
    """Return one QA to an authenticated Family or Owner reader."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()
    return _to_response(qa)


def create_question(db: Session, *, user: User, payload: QACreate) -> QAResponse:
    """Create a complete unanswered QA for the current Family user."""

    _require_family(user)
    qa = QA(
        asked_by=user.id,
        asker=user,
        question=payload.question,
        status=QAStatus.UNANSWERED,
    )
    add_qa(db, qa)
    _commit_and_refresh(db, qa)
    return _to_response(qa)


def upsert_answer(
    db: Session,
    *,
    user: User,
    qa_id: UUID,
    payload: QAAnswerUpsert,
) -> QAResponse:
    """Atomically add or replace the one current answer for a QA."""

    _require_owner(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    qa.answer = payload.answer
    qa.answered_by = user.id
    qa.answerer = user
    qa.answered_at = datetime.now(UTC)
    qa.status = QAStatus.ANSWERED
    _commit_and_refresh(db, qa)
    return _to_response(qa)


def _to_response(qa: QA) -> QAResponse:
    asker_display_name = getattr(qa.asker, "display_name", None)
    if not isinstance(asker_display_name, str):
        raise RuntimeError("QA asker relationship is not loaded")

    answerer_display_name = getattr(qa.answerer, "display_name", None)
    return QAResponse(
        id=qa.id,
        asked_by=qa.asked_by,
        asked_by_display_name=asker_display_name,
        question=qa.question,
        answer=qa.answer,
        answered_by=qa.answered_by,
        answered_by_display_name=(
            answerer_display_name if isinstance(answerer_display_name, str) else None
        ),
        status=qa.status,
        answered_at=qa.answered_at,
        created_at=qa.created_at,
        updated_at=qa.updated_at,
    )


def _require_reader(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(status_code=403, code="FORBIDDEN", message="QA access is not allowed")


def _require_family(user: User) -> None:
    if user.role is not UserRole.FAMILY:
        raise AppError(status_code=403, code="FORBIDDEN", message="Family access is required")


def _require_owner(user: User) -> None:
    if user.role is not UserRole.OWNER:
        raise AppError(status_code=403, code="FORBIDDEN", message="Owner access is required")


def _qa_not_found() -> AppError:
    return AppError(status_code=404, code="QA_NOT_FOUND", message="QA was not found")


def _commit_and_refresh(db: Session, qa: QA) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(qa)
