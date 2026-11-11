"""HTTP endpoints for authenticated QA reading, asking, and answering."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, Pagination
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    require_family_access,
    validate_csrf_request,
)
from app.modules.qas.schemas import (
    QACreate,
    QAAnswerCreate,
    QAAnswerUpdate,
    QAAnswerUpsert,
    QAResponse,
)
from app.modules.qas.service import (
    add_answer_to_qa,
    create_question,
    delete_qa_answer_for_user,
    delete_question_for_user,
    get_qa_for_user_or_404,
    list_qas_for_user,
    update_qa_answer,
    upsert_answer,
)


router = APIRouter(prefix="/qas", tags=["qas"])


@router.get("", response_model=Page[QAResponse])
def list_qa_records(
    pagination: Pagination,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> Page[QAResponse]:
    return list_qas_for_user(db, user=current_user.user, pagination=pagination)


@router.get("/{qa_id}", response_model=QAResponse)
def get_qa_record(
    qa_id: UUID,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    return get_qa_for_user_or_404(db, user=current_user.user, qa_id=qa_id)


@router.post("", response_model=QAResponse, status_code=status.HTTP_201_CREATED)
def create_qa_endpoint(
    payload: QACreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return create_question(db, user=current_user.user, payload=payload)


@router.delete("/{qa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qa_endpoint(
    qa_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> None:
    validate_csrf_request(request, current_user.session_id)
    delete_question_for_user(db, user=current_user.user, qa_id=qa_id)


@router.post("/{qa_id}/answers", response_model=QAResponse, status_code=status.HTTP_201_CREATED)
def add_qa_answer_endpoint(
    qa_id: UUID,
    payload: QAAnswerCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return add_answer_to_qa(db, user=current_user.user, qa_id=qa_id, payload=payload)


@router.put("/{qa_id}/answers/{answer_id}", response_model=QAResponse)
def update_qa_answer_endpoint(
    qa_id: UUID,
    answer_id: UUID,
    payload: QAAnswerUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return update_qa_answer(
        db,
        user=current_user.user,
        qa_id=qa_id,
        answer_id=answer_id,
        payload=payload,
    )


@router.delete("/{qa_id}/answers/{answer_id}", response_model=QAResponse)
def delete_qa_answer_endpoint(
    qa_id: UUID,
    answer_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return delete_qa_answer_for_user(
        db,
        user=current_user.user,
        qa_id=qa_id,
        answer_id=answer_id,
    )


@router.put("/{qa_id}/answer", response_model=QAResponse)
def upsert_qa_answer_endpoint(
    qa_id: UUID,
    payload: QAAnswerUpsert,
    request: Request,
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return upsert_answer(db, user=current_user.user, qa_id=qa_id, payload=payload)
