from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.qas.models import QA, QAAnswer, QAStatus
from app.modules.qas.repository import add_qa, get_qa, list_qas


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole, label: str):
    return create_user(
        test_session,
        login_name=f"qa-repository-{label}-{uuid4().hex}",
        display_name=f"Repository {label}",
        role=role,
        plain_password=PASSWORD,
    )


def test_qa_repository_returns_all_questions_with_actors_and_stable_pagination(
    test_session: Session,
) -> None:
    family_a = create_account(test_session, UserRole.FAMILY, "Family A")
    family_b = create_account(test_session, UserRole.FAMILY, "Family B")
    owner = create_account(test_session, UserRole.OWNER, "Owner")
    now = datetime.now(UTC)
    older = QA(
        asked_by=family_a.id,
        question="Older question",
        is_proxy=True,
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )
    answered = QA(
        asked_by=family_b.id,
        question="New answered question",
        status=QAStatus.ANSWERED,
        created_at=now,
        updated_at=now,
    )
    test_session.add_all([older, answered])
    test_session.flush()

    ans = QAAnswer(
        qa_id=answered.id,
        author_id=owner.id,
        content="Current answer",
        is_proxy=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(ans)
    test_session.flush()

    items, total = list_qas(test_session, offset=0, limit=1)
    loaded = get_qa(test_session, answered.id)

    assert total == 2
    assert [qa.id for qa in items] == [answered.id]
    assert loaded is not None
    assert loaded.asker.display_name == "Repository Family B"
    assert len(loaded.answers) == 1
    assert loaded.answers[0].author.display_name == "Repository Owner"
    assert loaded.answers[0].is_proxy is True


def test_add_qa_leaves_commit_to_service(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Staging Family")
    qa = QA(asked_by=family.id, question="Staged question")

    add_qa(test_session, qa)
    test_session.flush()

    assert test_session.get(QA, qa.id) == qa
    assert test_session.in_transaction()
