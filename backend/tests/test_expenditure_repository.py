from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.expenditures.models import Expenditure
from app.modules.expenditures.repository import (
    add_expenditure,
    delete_expenditure,
    get_expenditure,
    list_expenditures,
)


PASSWORD = "test-password-123"


def create_owner(test_session: Session):
    return create_user(
        test_session,
        login_name=f"expenditure-repository-owner-{uuid4().hex}",
        display_name="Repository Owner",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )


def make_expenditure(owner_id, *, spent_on: date, created_at: datetime, category: str) -> Expenditure:
    return Expenditure(
        created_by=owner_id,
        spent_on=spent_on,
        amount=Decimal("1234.5600"),
        currency="CNY",
        category=category,
        description=f"Test description for {category}",
        created_at=created_at,
        updated_at=created_at,
    )


def test_expenditure_repository_orders_by_business_date_and_paginates(test_session: Session) -> None:
    owner = create_owner(test_session)
    now = datetime.now(UTC)
    records = [
        make_expenditure(
            owner.id,
            spent_on=date(2026, 7, 27),
            created_at=now,
            category="Older date",
        ),
        make_expenditure(
            owner.id,
            spent_on=date(2026, 7, 28),
            created_at=now - timedelta(minutes=1),
            category="New date earlier creation",
        ),
        make_expenditure(
            owner.id,
            spent_on=date(2026, 7, 28),
            created_at=now,
            category="New date latest creation",
        ),
    ]
    test_session.add_all(records)
    test_session.flush()

    items, total = list_expenditures(test_session, offset=0, limit=2)
    loaded = get_expenditure(test_session, records[2].id)

    assert total == 3
    assert [item.category for item in items] == [
        "New date latest creation",
        "New date earlier creation",
    ]
    assert loaded is not None
    assert loaded.amount == Decimal("1234.5600")
    assert loaded.creator.display_name == "Repository Owner"


def test_add_and_delete_expenditure_leave_commit_to_service(test_session: Session) -> None:
    owner = create_owner(test_session)
    expenditure = make_expenditure(
        owner.id,
        spent_on=date(2026, 7, 28),
        created_at=datetime.now(UTC),
        category="Staged",
    )

    add_expenditure(test_session, expenditure)
    test_session.flush()
    assert test_session.get(Expenditure, expenditure.id) == expenditure

    delete_expenditure(test_session, expenditure)
    test_session.flush()
    assert test_session.get(Expenditure, expenditure.id) is None
