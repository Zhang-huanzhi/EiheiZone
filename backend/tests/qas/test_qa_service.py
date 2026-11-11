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
from app.modules.qas.schemas import (
    QACreate,
    QAAnswerCreate,
    QAAnswerUpdate,
    QAAnswerUpsert,
)
from app.modules.qas.service import (
    add_answer_to_qa,
    create_question,
    delete_qa_answer_for_user,
    get_qa_for_user_or_404,
    list_qas_for_user,
    update_qa_answer,
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
        payload=QACreate(question="Can everyone read this question?", is_proxy=True),
    )
    family_page = list_qas_for_user(test_session, user=family_b, pagination=PaginationParams())
    owner_detail = get_qa_for_user_or_404(test_session, user=owner, qa_id=created.id)

    assert created.asked_by == family_a.id
    assert created.asked_by_display_name == "Service Family A"
    assert created.is_proxy is True
    assert created.status is QAStatus.UNANSWERED
    assert created.answers_count == 0
    assert created.answers == []
    assert [item.id for item in family_page.items] == [created.id]
    assert owner_detail.id == created.id


def test_service_allows_both_family_and_owner_to_ask_and_answer(
    test_session: Session,
) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Family")
    owner = create_account(test_session, UserRole.OWNER, "Owner")
    question = create_question(
        test_session,
        user=owner,
        payload=QACreate(question="Can family answer this question?"),
    )

    # Family answers
    family_answer = add_answer_to_qa(
        test_session,
        user=family,
        qa_id=question.id,
        payload=QAAnswerCreate(content="Yes, family can answer too!", is_proxy=True),
    )

    # Owner also answers
    owner_answer = add_answer_to_qa(
        test_session,
        user=owner,
        qa_id=question.id,
        payload=QAAnswerCreate(content="Owner adds another perspective."),
    )

    assert family_answer.status is QAStatus.ANSWERED
    assert family_answer.answers_count == 1
    assert family_answer.answers[0].content == "Yes, family can answer too!"
    assert family_answer.answers[0].is_proxy is True

    assert owner_answer.answers_count == 2
    assert owner_answer.status is QAStatus.ANSWERED
    assert owner_answer.answers[1].content == "Owner adds another perspective."
    assert owner_answer.answers[1].is_proxy is False


def test_update_and_delete_answer_permissions(test_session: Session) -> None:
    family_a = create_account(test_session, UserRole.FAMILY, "Author Family")
    family_b = create_account(test_session, UserRole.FAMILY, "Other Family")
    owner = create_account(test_session, UserRole.OWNER, "Owner")

    question = create_question(
        test_session,
        user=family_a,
        payload=QACreate(question="Question for testing update/delete"),
    )
    res = add_answer_to_qa(
        test_session,
        user=family_a,
        qa_id=question.id,
        payload=QAAnswerCreate(content="Original answer"),
    )
    answer_id = res.answers[0].id

    # Other family cannot update
    with pytest.raises(AppError) as error:
        update_qa_answer(
            test_session,
            user=family_b,
            qa_id=question.id,
            answer_id=answer_id,
            payload=QAAnswerUpdate(content="Hacked answer"),
        )
    assert error.value.status_code == 403

    # Owner can update
    updated_by_owner = update_qa_answer(
        test_session,
        user=owner,
        qa_id=question.id,
        answer_id=answer_id,
        payload=QAAnswerUpdate(content="Owner updated answer", is_proxy=False),
    )
    assert updated_by_owner.answers[0].content == "Owner updated answer"
    assert updated_by_owner.answers[0].is_proxy is False

    # Author can delete; question reverts to UNANSWERED
    after_delete = delete_qa_answer_for_user(
        test_session,
        user=family_a,
        qa_id=question.id,
        answer_id=answer_id,
    )
    assert after_delete.status is QAStatus.UNANSWERED
    assert after_delete.answers_count == 0


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
    assert len(stored.answers) == 0


def test_qa_detail_not_found_uses_module_error(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Missing Family")

    with pytest.raises(AppError) as error:
        get_qa_for_user_or_404(test_session, user=family, qa_id=uuid4())

    assert error.value.status_code == 404
    assert error.value.code == "QA_NOT_FOUND"
