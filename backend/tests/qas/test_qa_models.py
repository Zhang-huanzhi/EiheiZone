from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.qas.models import QA, QAAnswer, QAStatus


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole):
    return create_user(
        test_session,
        login_name=f"qa-model-{role.value}-{uuid4().hex}",
        display_name=f"QA Model {role.value.title()}",
        role=role,
        plain_password=PASSWORD,
    )


def test_qa_defaults_create_a_complete_unanswered_state(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    qa = QA(asked_by=family.id, question="How is the project going?")

    test_session.add(qa)
    test_session.flush()

    assert qa.id is not None
    assert qa.status is QAStatus.UNANSWERED
    assert qa.is_proxy is False
    assert qa.answers == []
    assert qa.created_at.tzinfo is not None
    assert qa.updated_at.tzinfo is not None


@pytest.mark.parametrize(
    "qa",
    [
        QA(question=" "),
        QA(question="q" * 2001),
    ],
)
def test_qa_database_rejects_invalid_question_text(test_session: Session, qa: QA) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    qa.asked_by = family.id

    with pytest.raises(IntegrityError):
        with test_session.begin_nested():
            test_session.add(qa)
            test_session.flush()


def test_qa_relationships_and_answers_cascade(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    owner = create_account(test_session, UserRole.OWNER)
    qa = QA(
        asked_by=family.id,
        question="A complete question",
        is_proxy=True,
        status=QAStatus.ANSWERED,
    )
    test_session.add(qa)
    test_session.flush()

    answer = QAAnswer(
        qa_id=qa.id,
        author_id=owner.id,
        content="A complete answer",
        is_proxy=True,
    )
    test_session.add(answer)
    test_session.flush()

    test_session.expire(qa, ["asker", "answers"])
    assert qa.asker.id == family.id
    assert len(qa.answers) == 1
    assert qa.answers[0].author_id == owner.id
    assert qa.answers[0].is_proxy is True

    # Test cascade delete
    test_session.delete(qa)
    test_session.flush()
    assert test_session.get(QAAnswer, answer.id) is None
