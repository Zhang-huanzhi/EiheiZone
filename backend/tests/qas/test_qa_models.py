from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.qas.models import QA, QAStatus


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
    assert qa.answer is None
    assert qa.answered_by is None
    assert qa.answered_at is None
    assert qa.created_at.tzinfo is not None
    assert qa.updated_at.tzinfo is not None


@pytest.mark.parametrize(
    ("status", "answer", "include_answerer", "answered_at"),
    [
        (QAStatus.ANSWERED, None, False, None),
        (QAStatus.UNANSWERED, "Unexpected", True, datetime.now(UTC)),
        (QAStatus.ANSWERED, "Incomplete", False, datetime.now(UTC)),
    ],
)
def test_qa_database_rejects_inconsistent_answer_states(
    test_session: Session,
    status: QAStatus,
    answer: str | None,
    include_answerer: bool,
    answered_at: datetime | None,
) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    owner = create_account(test_session, UserRole.OWNER)

    with pytest.raises(IntegrityError):
        with test_session.begin_nested():
            test_session.add(
                QA(
                    asked_by=family.id,
                    question="Invalid state",
                    answer=answer,
                    answered_by=owner.id if include_answerer else None,
                    status=status,
                    answered_at=answered_at,
                )
            )
            test_session.flush()


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


def test_qa_relationships_distinguish_asker_and_answerer(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    owner = create_account(test_session, UserRole.OWNER)
    qa = QA(
        asked_by=family.id,
        question="A complete question",
        answer="A complete answer",
        answered_by=owner.id,
        status=QAStatus.ANSWERED,
        answered_at=datetime.now(UTC),
    )
    test_session.add(qa)
    test_session.flush()
    test_session.expire(qa, ["asker", "answerer"])

    assert qa.asker.id == family.id
    assert qa.answerer is not None
    assert qa.answerer.id == owner.id
