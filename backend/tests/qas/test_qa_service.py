from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import PaginationParams
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.qas.models import QAStatus
from app.modules.qas.repository import get_qa
from app.modules.qas.schemas import QACreate, QAAnswerUpsert
from app.modules.qas.service import (
    create_question,
    get_qa_for_user_or_404,
    list_qas_for_user,
    upsert_answer,
)


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole, label: str):
    return create_user(
        test_session,
        login_name=f"qa-service-{label}-{uuid4().hex}",
        display_name=f"Service {label}",
        role=role,
        plain_password=PASSWORD,
    )


def test_family_question_is_visible_to_other_family_and_owner(test_session: Session) -> None:
    family_a = create_account(test_session, UserRole.FAMILY, "Family A")
    family_b = create_account(test_session, UserRole.FAMILY, "Family B")
    owner = create_account(test_session, UserRole.OWNER, "Owner")

    created = create_question(
        test_session,
        user=family_a,
        payload=QACreate(question="Can everyone read this question?"),
    )
    family_page = list_qas_for_user(test_session, user=family_b, pagination=PaginationParams())
    owner_detail = get_qa_for_user_or_404(test_session, user=owner, qa_id=created.id)

    assert created.asked_by == family_a.id
    assert created.asked_by_display_name == "Service Family A"
    assert created.status is QAStatus.UNANSWERED
    assert created.answer is None
    assert created.answered_by is None
    assert created.answered_at is None
    assert [item.id for item in family_page.items] == [created.id]
    assert owner_detail.id == created.id


def test_service_allows_family_and_owner_questions_but_only_owner_answers(
    test_session: Session,
) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Family")
    owner = create_account(test_session, UserRole.OWNER, "Owner")
    family_question = create_question(
        test_session,
        user=family,
        payload=QACreate(question="Who may perform each action?"),
    )

    owner_question = create_question(
        test_session,
        user=owner,
        payload=QACreate(question="Can Owner also ask a question?"),
    )
    with pytest.raises(AppError) as family_answer_error:
        upsert_answer(
            test_session,
            user=family,
            qa_id=family_question.id,
            payload=QAAnswerUpsert(answer="Family must not answer"),
        )

    assert family_question.status is QAStatus.UNANSWERED
    assert owner_question.asked_by == owner.id
    assert owner_question.asked_by_display_name == "Service Owner"
    assert owner_question.status is QAStatus.UNANSWERED
    assert family_answer_error.value.status_code == 403


def test_owner_adds_and_replaces_one_complete_answer(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Answer Family")
    owner = create_account(test_session, UserRole.OWNER, "Answer Owner")
    created = create_question(
        test_session,
        user=family,
        payload=QACreate(question="What is the current answer?"),
    )

    first = upsert_answer(
        test_session,
        user=owner,
        qa_id=created.id,
        payload=QAAnswerUpsert(answer="First answer"),
    )
    first_answered_at = first.answered_at
    replaced = upsert_answer(
        test_session,
        user=owner,
        qa_id=created.id,
        payload=QAAnswerUpsert(answer="Replacement answer"),
    )

    assert replaced.id == created.id
    assert replaced.question == created.question
    assert replaced.answer == "Replacement answer"
    assert replaced.answered_by == owner.id
    assert replaced.answered_by_display_name == "Service Answer Owner"
    assert replaced.status is QAStatus.ANSWERED
    assert first_answered_at is not None
    assert replaced.answered_at is not None
    assert replaced.answered_at >= first_answered_at


def test_answer_service_rolls_back_when_commit_fails(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Rollback Family")
    owner = create_account(test_session, UserRole.OWNER, "Rollback Owner")
    created = create_question(
        test_session,
        user=family,
        payload=QACreate(question="This answer should roll back"),
    )
    rollback_calls = 0

    def fail_commit() -> None:
        raise OperationalError("COMMIT", {}, None)

    def record_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        test_session.expire_all()

    monkeypatch.setattr(test_session, "commit", fail_commit)
    monkeypatch.setattr(test_session, "rollback", record_rollback)

    with pytest.raises(OperationalError):
        upsert_answer(
            test_session,
            user=owner,
            qa_id=created.id,
            payload=QAAnswerUpsert(answer="Failed answer"),
        )

    stored = get_qa(test_session, created.id)
    assert rollback_calls == 1
    assert stored is not None
    assert stored.status is QAStatus.UNANSWERED
    assert stored.answer is None
    assert stored.answered_by is None
    assert stored.answered_at is None


def test_qa_detail_not_found_uses_module_error(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Missing Family")

    with pytest.raises(AppError) as error:
        get_qa_for_user_or_404(test_session, user=family, qa_id=uuid4())

    assert error.value.status_code == 404
    assert error.value.code == "QA_NOT_FOUND"
