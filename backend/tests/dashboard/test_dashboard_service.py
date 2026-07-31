from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.dashboard.service import DASHBOARD_ITEM_LIMIT, get_dashboard
from app.modules.expenditures.schemas import ExpenditureCreate
from app.modules.expenditures.service import create_expenditure
from app.modules.posts.schemas import PostCreate
from app.modules.posts.service import create_post
from app.modules.qas.schemas import QACreate, QAAnswerUpsert
from app.modules.qas.service import (
    create_question,
    list_unanswered_qas_for_user,
    upsert_answer,
)


PASSWORD = "test-password-123"


def create_account(test_session: Session, role: UserRole, label: str):
    return create_user(
        test_session,
        login_name=f"dashboard-service-{label}-{uuid4().hex}",
        display_name=f"Dashboard {label}",
        role=role,
        plain_password=PASSWORD,
    )


def test_dashboard_aggregates_fixed_recent_sections_and_true_totals(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Family")
    owner = create_account(test_session, UserRole.OWNER, "Owner")

    for index in range(DASHBOARD_ITEM_LIMIT + 1):
        create_post(
            test_session,
            user=owner,
            payload=PostCreate(title=f"Post {index}", body=f"Body {index}"),
        )

    pending = create_question(
        test_session,
        user=family,
        payload=QACreate(question="Older unanswered question"),
    )
    for index in range(DASHBOARD_ITEM_LIMIT):
        answered = create_question(
            test_session,
            user=family,
            payload=QACreate(question=f"Answered question {index}"),
        )
        upsert_answer(
            test_session,
            user=owner,
            qa_id=answered.id,
            payload=QAAnswerUpsert(answer=f"Answer {index}"),
        )

    first_day = date(2026, 7, 20)
    for index in range(DASHBOARD_ITEM_LIMIT + 1):
        create_expenditure(
            test_session,
            user=owner,
            payload=ExpenditureCreate(
                spent_on=(first_day + timedelta(days=index)).isoformat(),
                amount=f"{index + 1}.0000",
                currency="CNY",
                category=f"Category {index}",
                description=f"Test expenditure {index}",
            ),
        )

    def fail_commit() -> None:
        raise AssertionError("Dashboard reads must not commit")

    monkeypatch.setattr(test_session, "commit", fail_commit)
    dashboard = get_dashboard(test_session, user=family)
    owner_pending = list_unanswered_qas_for_user(
        test_session,
        user=owner,
        pagination=PaginationParams(offset=0, limit=DASHBOARD_ITEM_LIMIT),
    )

    assert len(dashboard.posts.items) == DASHBOARD_ITEM_LIMIT
    assert dashboard.posts.total == DASHBOARD_ITEM_LIMIT + 1
    assert len(dashboard.qas.items) == DASHBOARD_ITEM_LIMIT
    assert dashboard.qas.total == DASHBOARD_ITEM_LIMIT + 1
    assert pending.id not in {item.id for item in dashboard.qas.items}
    assert len(dashboard.expenditures.items) == DASHBOARD_ITEM_LIMIT
    assert dashboard.expenditures.total == DASHBOARD_ITEM_LIMIT + 1
    assert [item.spent_on for item in dashboard.expenditures.items] == sorted(
        [item.spent_on for item in dashboard.expenditures.items],
        reverse=True,
    )
    assert dashboard.unanswered_qas.total == 1
    assert [item.id for item in dashboard.unanswered_qas.items] == [pending.id]
    assert [item.id for item in owner_pending.items] == [pending.id]


def test_dashboard_returns_independent_empty_sections(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY, "Empty Family")

    dashboard = get_dashboard(test_session, user=family)

    assert dashboard.posts.items == []
    assert dashboard.posts.total == 0
    assert dashboard.qas.items == []
    assert dashboard.qas.total == 0
    assert dashboard.expenditures.items == []
    assert dashboard.expenditures.total == 0
    assert dashboard.unanswered_qas.items == []
    assert dashboard.unanswered_qas.total == 0
