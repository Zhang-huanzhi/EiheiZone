"""Client-safe input and output schemas for Expenditure endpoints."""

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.expenditures.currencies import CurrencyCode, normalize_currency_code


MAX_CATEGORY_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 2000
AMOUNT_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]{1,4})?$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
ExpenditureAmount = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]


def _parse_amount(value: object) -> Decimal:
    if not isinstance(value, str) or AMOUNT_PATTERN.fullmatch(value) is None:
        raise ValueError("Amount must be a plain decimal string with at most 4 decimal places")
    return Decimal(value)


def _parse_spent_on(value: object) -> date:
    if not isinstance(value, str) or DATE_PATTERN.fullmatch(value) is None:
        raise ValueError("Spent on must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Spent on must be a valid date") from error


def _normalize_category(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Category must not be blank")
    if len(normalized) > MAX_CATEGORY_LENGTH:
        raise ValueError("Category must contain at most 80 characters")
    return normalized


def _validate_description(value: str) -> str:
    if not value.strip():
        raise ValueError("Description must not be blank")
    if len(value) > MAX_DESCRIPTION_LENGTH:
        raise ValueError("Description must contain at most 2000 characters")
    return value


class ExpenditureCreate(BaseModel):
    """Accept only the business fields Owner may set for a new expenditure."""

    model_config = ConfigDict(extra="forbid")

    spent_on: date
    amount: ExpenditureAmount
    currency: CurrencyCode
    category: str
    description: str

    @field_validator("spent_on", mode="before")
    @classmethod
    def parse_spent_on(cls, value: object) -> date:
        return _parse_spent_on(value)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        return _parse_amount(value)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> CurrencyCode:
        if not isinstance(value, str):
            raise ValueError("Currency must be a string")
        return normalize_currency_code(value)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return _normalize_category(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _validate_description(value)


class ExpenditureUpdate(BaseModel):
    """Accept a non-empty partial update without nullable business fields."""

    model_config = ConfigDict(extra="forbid")

    spent_on: date | None = None
    amount: ExpenditureAmount | None = None
    currency: CurrencyCode | None = None
    category: str | None = None
    description: str | None = None

    @field_validator("spent_on", mode="before")
    @classmethod
    def parse_optional_spent_on(cls, value: object) -> date | None:
        return None if value is None else _parse_spent_on(value)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_optional_amount(cls, value: object) -> Decimal | None:
        return None if value is None else _parse_amount(value)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_optional_currency(cls, value: object) -> CurrencyCode | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Currency must be a string")
        return normalize_currency_code(value)

    @field_validator("category")
    @classmethod
    def normalize_optional_category(cls, value: str | None) -> str | None:
        return None if value is None else _normalize_category(value)

    @field_validator("description")
    @classmethod
    def validate_optional_description(cls, value: str | None) -> str | None:
        return None if value is None else _validate_description(value)

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> "ExpenditureUpdate":
        allowed_fields = {"spent_on", "amount", "currency", "category", "description"}
        supplied_fields = self.model_fields_set & allowed_fields
        if not supplied_fields:
            raise ValueError("At least one Expenditure field must be supplied")
        for field_name in supplied_fields:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null")
        return self


class ExpenditureResponse(BaseModel):
    """Return exact expenditure data and only the creator information pages need."""

    id: UUID
    created_by: UUID
    created_by_display_name: str = Field(min_length=1, max_length=80)
    spent_on: date
    amount: ExpenditureAmount
    currency: CurrencyCode
    category: str = Field(min_length=1, max_length=MAX_CATEGORY_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    created_at: datetime
    updated_at: datetime
