from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import PaginationParams
from app.modules.auth.models import UserRole
from app.modules.auth.service import create_user
from app.modules.expenditures.schemas import ExpenditureCreate, ExpenditureUpdate
from app.modules.expenditures.service import (
    create_expenditure,
    get_expenditure_for_user_or_404,
    list_expenditures_for_user,
    remove_expenditure,
    update_expenditure,
)


PASSWORD = "test-password-123"
BASE_INPUT = {
    "spent_on": "2026-07-28",
    "amount": "1234.5600",
    "currency": "CNY",
    "category": "Equipment",
    "description": "Test equipment purchase",
}


def create_account(test_session: Session, role: UserRole, label: str):
    return create_user(
        test_session,
        login_name=f"expenditure-service-{label}-{uuid4().hex}",
        display_name=f"Service {label}",
        role=role,
        plain_password=PASSWORD,
    )


def test_owner_create_is_visible_to_family_with_exact_amount(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER, "Owner")
    family = create_account(test_session, UserRole.FAMILY, "Family")

    created = create_expenditure(
        test_session,
        user=owner,
        payload=ExpenditureCreate(**BASE_INPUT),
    )
    page = list_expenditures_for_user(test_session, user=family, pagination=PaginationParams())

    assert created.created_by == owner.id
    assert created.created_by_display_name == "Service Owner"
    assert created.amount == Decimal("1234.5600")
    assert page.items[0].id == created.id


def test_service_enforces_owner_writes_and_partial_update(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER, "Write Owner")
    family = create_account(test_session, UserRole.FAMILY, "Write Family")
    created = create_expenditure(
        test_session,
        user=owner,
        payload=ExpenditureCreate(**BASE_INPUT),
    )

    with pytest.raises(AppError) as error:
        update_expenditure(
            test_session,
            user=family,
            expenditure_id=created.id,
            payload=ExpenditureUpdate(category="Forbidden"),
        )
    updated = update_expenditure(
        test_session,
        user=owner,
        expenditure_id=created.id,
        payload=ExpenditureUpdate(category="Updated category"),
    )

    assert error.value.status_code == 403
    assert updated.category == "Updated category"
    assert updated.amount == Decimal("1234.5600")
    assert updated.description == BASE_INPUT["description"]
    assert updated.created_by == owner.id


def test_owner_hard_deletes_expenditure(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER, "Delete Owner")
    created = create_expenditure(
        test_session,
        user=owner,
        payload=ExpenditureCreate(**BASE_INPUT),
    )

    remove_expenditure(test_session, user=owner, expenditure_id=created.id)

    with pytest.raises(AppError) as error:
        get_expenditure_for_user_or_404(
            test_session,
            user=owner,
            expenditure_id=created.id,
        )
    assert error.value.code == "EXPENDITURE_NOT_FOUND"


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
def test_expenditure_write_services_roll_back_when_commit_fails(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    owner = create_account(test_session, UserRole.OWNER, f"Rollback {operation}")
    created = create_expenditure(
        test_session,
        user=owner,
        payload=ExpenditureCreate(**BASE_INPUT),
    )
    rollback_calls = 0

    def fail_commit() -> None:
        raise OperationalError("COMMIT", {}, None)

    def record_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1

    monkeypatch.setattr(test_session, "commit", fail_commit)
    monkeypatch.setattr(test_session, "rollback", record_rollback)

    with pytest.raises(OperationalError):
        if operation == "create":
            create_expenditure(
                test_session,
                user=owner,
                payload=ExpenditureCreate(**{**BASE_INPUT, "category": "New"}),
            )
        elif operation == "update":
            update_expenditure(
                test_session,
                user=owner,
                expenditure_id=created.id,
                payload=ExpenditureUpdate(category="Failed update"),
            )
        else:
            remove_expenditure(test_session, user=owner, expenditure_id=created.id)

    assert rollback_calls == 1
