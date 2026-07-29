"""Database access helpers for Expenditure records."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.expenditures.models import Expenditure


def list_expenditures(
    db: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[list[Expenditure], int]:
    """Return every family expenditure in stable business-date order."""

    statement = (
        select(Expenditure)
        .options(joinedload(Expenditure.creator))
        .order_by(
            Expenditure.spent_on.desc(),
            Expenditure.created_at.desc(),
            Expenditure.id.desc(),
        )
    )
    items = list(db.scalars(statement.offset(offset).limit(limit)))
    total = db.scalar(select(func.count()).select_from(Expenditure))
    return items, int(total or 0)


def get_expenditure(db: Session, expenditure_id: UUID) -> Expenditure | None:
    """Return one expenditure with its client-safe creator relationship."""

    statement = (
        select(Expenditure)
        .options(joinedload(Expenditure.creator))
        .where(Expenditure.id == expenditure_id)
    )
    return db.scalar(statement)


def add_expenditure(db: Session, expenditure: Expenditure) -> None:
    """Stage a new expenditure for the surrounding service transaction."""

    db.add(expenditure)


def delete_expenditure(db: Session, expenditure: Expenditure) -> None:
    """Stage a hard deletion without committing it."""

    db.delete(expenditure)
