from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.expenditures.models import Expenditure


PASSWORD = "test-password-123"


def create_owner(test_session: Session):
    return create_user(
        test_session,
        login_name=f"expenditure-model-owner-{uuid4().hex}",
        display_name="Expenditure Model Owner",
        role=UserRole.OWNER,
        plain_password=PASSWORD,
    )


def test_expenditure_preserves_decimal_date_and_utc_fields(test_session: Session) -> None:
    owner = create_owner(test_session)
    expenditure = Expenditure(
        created_by=owner.id,
        spent_on=date(2026, 7, 28),
        amount=Decimal("1234.5600"),
        currency="CNY",
        category="Equipment",
        description="Test equipment purchase",
    )

    test_session.add(expenditure)
    test_session.flush()

    assert expenditure.id is not None
    assert expenditure.spent_on == date(2026, 7, 28)
    assert expenditure.amount == Decimal("1234.5600")
    assert not isinstance(expenditure.amount, float)
    assert expenditure.created_at.tzinfo is not None
    assert expenditure.updated_at.tzinfo is not None


@pytest.mark.parametrize(
    ("amount", "category", "description"),
    [
        (Decimal("0"), "Equipment", "Test description"),
        (Decimal("-1"), "Equipment", "Test description"),
        (Decimal("1"), "   ", "Test description"),
        (Decimal("1"), "Equipment", "\n\t"),
    ],
)
def test_expenditure_database_rejects_invalid_values(
    test_session: Session,
    amount: Decimal,
    category: str,
    description: str,
) -> None:
    owner = create_owner(test_session)

    with pytest.raises(IntegrityError):
        with test_session.begin_nested():
            test_session.add(
                Expenditure(
                    created_by=owner.id,
                    spent_on=date(2026, 7, 28),
                    amount=amount,
                    currency="CNY",
                    category=category,
                    description=description,
                )
            )
            test_session.flush()


def test_expenditure_creator_relationship_uses_owner_user(test_session: Session) -> None:
    owner = create_owner(test_session)
    expenditure = Expenditure(
        created_by=owner.id,
        spent_on=date(2026, 7, 28),
        amount=Decimal("10.0000"),
        currency="JPY",
        category="Travel",
        description="Test travel expense",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_session.add(expenditure)
    test_session.flush()
    test_session.expire(expenditure, ["creator"])

    assert expenditure.creator.id == owner.id
    assert expenditure.creator.display_name == "Expenditure Model Owner"
