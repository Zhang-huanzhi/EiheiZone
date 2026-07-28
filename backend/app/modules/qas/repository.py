"""Database access helpers for QA records."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.qas.models import QA


def list_qas(db: Session, *, offset: int, limit: int) -> tuple[list[QA], int]:
    """Return every family QA in stable newest-first order."""

    statement = (
        select(QA)
        .options(joinedload(QA.asker), joinedload(QA.answerer))
        .order_by(QA.created_at.desc(), QA.id.desc())
    )
    items = list(db.scalars(statement.offset(offset).limit(limit)))
    total = db.scalar(select(func.count()).select_from(QA))
    return items, int(total or 0)


def get_qa(db: Session, qa_id: UUID) -> QA | None:
    """Return one QA and the client-safe actor data needed by its response."""

    statement = (
        select(QA)
        .options(joinedload(QA.asker), joinedload(QA.answerer))
        .where(QA.id == qa_id)
    )
    return db.scalar(statement)


def add_qa(db: Session, qa: QA) -> None:
    """Stage a new QA for the surrounding service transaction."""

    db.add(qa)
