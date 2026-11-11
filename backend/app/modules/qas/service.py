"""QA business rules, multi-member answers, state consistency, and transactions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import Page, PaginationParams
from app.modules.auth.models import User, UserRole
from app.modules.notifications.service import enqueue_answer, enqueue_new_question
from app.modules.qas.models import QA, QAAnswer, QAStatus
from app.modules.qas.repository import (
    add_qa,
    add_qa_answer,
    delete_qa,
    delete_qa_answer,
    get_qa,
    get_qa_answer,
    list_qas,
    list_unanswered_qas,
)
from app.modules.qas.schemas import (
    QACreate,
    QAAnswerCreate,
    QAAnswerResponse,
    QAAnswerUpdate,
    QAAnswerUpsert,
    QAResponse,
)


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


def list_unanswered_qas_for_user(
    db: Session,
    *,
    user: User,
    pagination: PaginationParams,
) -> Page[QAResponse]:
    """Return pending family QAs with zero answers to an authenticated reader."""

    _require_reader(user)
    items, total = list_unanswered_qas(
        db,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[_to_response(qa) for qa in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


def get_qa_for_user_or_404(db: Session, *, user: User, qa_id: UUID) -> QAResponse:
    """Return one QA thread and all its answers to an authenticated reader."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()
    return _to_response(qa)


def create_question(db: Session, *, user: User, payload: QACreate) -> QAResponse:
    """Create an unanswered QA topic for the current Family or Owner user."""

    _require_questioner(user)
    qa = QA(
        id=uuid4(),
        asked_by=user.id,
        asker=user,
        question=payload.question,
        is_proxy=payload.is_proxy,
        status=QAStatus.UNANSWERED,
    )
    add_qa(db, qa)
    enqueue_new_question(db, qa_id=qa.id)
    _commit_and_refresh(db, qa)
    return _to_response(qa)


def add_answer_to_qa(
    db: Session,
    *,
    user: User,
    qa_id: UUID,
    payload: QAAnswerCreate,
) -> QAResponse:
    """Add a new answer to a QA topic from any authenticated Family or Owner user."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    answer = QAAnswer(
        id=uuid4(),
        qa_id=qa.id,
        author_id=user.id,
        author=user,
        content=payload.content,
        is_proxy=payload.is_proxy,
    )
    add_qa_answer(db, answer)
    qa.status = QAStatus.ANSWERED
    qa.updated_at = datetime.now(UTC)

    if user.id != qa.asked_by:
        enqueue_answer(db, qa_id=qa.id, asker_id=qa.asked_by)

    _commit_and_refresh(db, qa)
    return _to_response(qa)


def upsert_answer(
    db: Session,
    *,
    user: User,
    qa_id: UUID,
    payload: QAAnswerUpsert,
) -> QAResponse:
    """Add or update an answer (backward-compatible endpoint)."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    user_answers = [a for a in qa.answers if a.author_id == user.id]
    if user_answers:
        latest = user_answers[-1]
        latest.content = payload.answer
        latest.is_proxy = payload.is_proxy
        latest.updated_at = datetime.now(UTC)
    else:
        answer = QAAnswer(
            id=uuid4(),
            qa_id=qa.id,
            author_id=user.id,
            author=user,
            content=payload.answer,
            is_proxy=payload.is_proxy,
        )
        add_qa_answer(db, answer)

    qa.status = QAStatus.ANSWERED
    qa.updated_at = datetime.now(UTC)

    if user.id != qa.asked_by:
        enqueue_answer(db, qa_id=qa.id, asker_id=qa.asked_by)

    _commit_and_refresh(db, qa)
    return _to_response(qa)


def update_qa_answer(
    db: Session,
    *,
    user: User,
    qa_id: UUID,
    answer_id: UUID,
    payload: QAAnswerUpdate,
) -> QAResponse:
    """Update an existing answer by its author or an Owner."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    answer = get_qa_answer(db, answer_id)
    if answer is None or answer.qa_id != qa.id:
        raise AppError(status_code=404, code="ANSWER_NOT_FOUND", message="Answer was not found")

    _require_author_or_owner(user, answer.author_id)
    answer.content = payload.content
    answer.is_proxy = payload.is_proxy
    answer.updated_at = datetime.now(UTC)
    qa.updated_at = datetime.now(UTC)

    _commit_and_refresh(db, qa)
    return _to_response(qa)


def delete_qa_answer_for_user(
    db: Session,
    *,
    user: User,
    qa_id: UUID,
    answer_id: UUID,
) -> QAResponse:
    """Delete an answer by its author or an Owner and adjust QA status if needed."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    answer = get_qa_answer(db, answer_id)
    if answer is None or answer.qa_id != qa.id:
        raise AppError(status_code=404, code="ANSWER_NOT_FOUND", message="Answer was not found")

    _require_author_or_owner(user, answer.author_id)
    delete_qa_answer(db, answer)
    db.flush()

    # Re-evaluate remaining answers
    remaining_answers = [a for a in qa.answers if a.id != answer_id]
    qa.status = QAStatus.ANSWERED if remaining_answers else QAStatus.UNANSWERED
    qa.updated_at = datetime.now(UTC)

    _commit_and_refresh(db, qa)
    return _to_response(qa)


def delete_question_for_user(db: Session, *, user: User, qa_id: UUID) -> None:
    """Delete an entire QA thread by its asker or an Owner."""

    _require_reader(user)
    qa = get_qa(db, qa_id)
    if qa is None:
        raise _qa_not_found()

    _require_author_or_owner(user, qa.asked_by)
    delete_qa(db, qa)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def _to_response(qa: QA) -> QAResponse:
    asker_display_name = getattr(qa.asker, "display_name", None)
    if not isinstance(asker_display_name, str):
        raise RuntimeError("QA asker relationship is not loaded")

    answers_list: list[QAAnswerResponse] = []
    latest_answer: QAAnswer | None = None
    for a in qa.answers:
        author_display = getattr(a.author, "display_name", None)
        answers_list.append(
            QAAnswerResponse(
                id=a.id,
                qa_id=a.qa_id,
                author_id=a.author_id,
                author_display_name=author_display if isinstance(author_display, str) else "家人",
                content=a.content,
                is_proxy=a.is_proxy,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
        latest_answer = a

    legacy_answer = latest_answer.content if latest_answer else None
    legacy_answered_by = latest_answer.author_id if latest_answer else None
    legacy_answered_by_display = (
        getattr(latest_answer.author, "display_name", None) if latest_answer else None
    )
    legacy_answered_at = latest_answer.created_at if latest_answer else None

    return QAResponse(
        id=qa.id,
        asked_by=qa.asked_by,
        asked_by_display_name=asker_display_name,
        question=qa.question,
        is_proxy=qa.is_proxy,
        status=qa.status,
        answers_count=len(answers_list),
        answers=answers_list,
        answer=legacy_answer,
        answered_by=legacy_answered_by,
        answered_by_display_name=(
            legacy_answered_by_display if isinstance(legacy_answered_by_display, str) else None
        ),
        answered_at=legacy_answered_at,
        created_at=qa.created_at,
        updated_at=qa.updated_at,
    )


def _require_reader(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(status_code=403, code="FORBIDDEN", message="QA access is not allowed")


def _require_questioner(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Family or Owner access is required",
        )


def _require_author_or_owner(user: User, author_id: UUID) -> None:
    if user.role is not UserRole.OWNER and user.id != author_id:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Permission denied",
        )


def _qa_not_found() -> AppError:
    return AppError(status_code=404, code="QA_NOT_FOUND", message="QA was not found")


def _commit_and_refresh(db: Session, qa: QA) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(qa)
