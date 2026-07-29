from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.expenditures.currencies import CurrencyCode
from app.modules.expenditures.schemas import (
    ExpenditureCreate,
    ExpenditureResponse,
    ExpenditureUpdate,
)


BASE_INPUT = {
    "spent_on": "2026-07-28",
    "amount": "1234.5600",
    "currency": "CNY",
    "category": "Equipment",
    "description": "Test equipment purchase",
}


@pytest.mark.parametrize(
    "value",
    ["0.0001", "1", "001.2300", "99999999999999.9999"],
)
def test_expenditure_create_accepts_exact_decimal_string_boundaries(value: str) -> None:
    payload = ExpenditureCreate(**{**BASE_INPUT, "amount": value})

    assert isinstance(payload.amount, Decimal)
    assert payload.amount == Decimal(value)


@pytest.mark.parametrize(
    "value",
    [0, 1.25, Decimal("1.25"), "0", "0.0000", "-1", "1.23456", "1e3", "1,000.00", "999999999999999.9999"],
)
def test_expenditure_create_rejects_non_contract_amounts(value: object) -> None:
    with pytest.raises(ValidationError):
        ExpenditureCreate(**{**BASE_INPUT, "amount": value})


def test_expenditure_normalizes_currency_and_category() -> None:
    payload = ExpenditureCreate(
        **{
            **BASE_INPUT,
            "currency": " jpy ",
            "category": "  Travel  ",
        }
    )

    assert payload.currency is CurrencyCode.JPY
    assert payload.category == "Travel"


@pytest.mark.parametrize("value", ["ZZZ", "AB", "123", ""])
def test_expenditure_rejects_unsupported_currency(value: str) -> None:
    with pytest.raises(ValidationError):
        ExpenditureCreate(**{**BASE_INPUT, "currency": value})


@pytest.mark.parametrize("value", ["2026-02-29", "2026/07/28", "not-a-date", None])
def test_expenditure_rejects_invalid_business_date(value: object) -> None:
    with pytest.raises(ValidationError):
        ExpenditureCreate(**{**BASE_INPUT, "spent_on": value})


@pytest.mark.parametrize("field", ["card_number", "transaction_id", "address", "attachment", "created_by"])
def test_expenditure_rejects_extra_private_or_server_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        ExpenditureCreate(**{**BASE_INPUT, field: "not-stored"})


def test_expenditure_update_requires_non_null_supplied_field() -> None:
    with pytest.raises(ValidationError):
        ExpenditureUpdate()
    with pytest.raises(ValidationError):
        ExpenditureUpdate(amount=None)
    with pytest.raises(ValidationError):
        ExpenditureUpdate(card_number="not-stored")

    update = ExpenditureUpdate(amount="10.2500")
    assert update.amount == Decimal("10.2500")


def test_expenditure_response_serializes_decimal_as_json_string() -> None:
    response = ExpenditureResponse(
        id=uuid4(),
        created_by=uuid4(),
        created_by_display_name="Owner",
        spent_on=date(2026, 7, 28),
        amount=Decimal("1234.5600"),
        currency=CurrencyCode.CNY,
        category="Equipment",
        description="Test equipment purchase",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert '"amount":"1234.5600"' in response.model_dump_json()
    assert '"spent_on":"2026-07-28"' in response.model_dump_json()
