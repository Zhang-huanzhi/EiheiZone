"""HTTP endpoints for authenticated QA reading, asking, and answering."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, Pagination
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    require_family,
    require_family_access,
    require_owner,
    validate_csrf_request,
)
from app.modules.qas.schemas import QACreate, QAAnswerUpsert, QAResponse
from app.modules.qas.service import (
    create_question,
    get_qa_for_user_or_404,
    list_qas_for_user,
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
    current_user: CurrentUser = Depends(require_family),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return create_question(db, user=current_user.user, payload=payload)


@router.put("/{qa_id}/answer", response_model=QAResponse)
def upsert_qa_answer_endpoint(
    qa_id: UUID,
    payload: QAAnswerUpsert,
    request: Request,
    current_user: CurrentUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> QAResponse:
    validate_csrf_request(request, current_user.session_id)
    return upsert_answer(db, user=current_user.user, qa_id=qa_id, payload=payload)
