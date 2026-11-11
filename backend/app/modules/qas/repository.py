"""Database access helpers for QA records and answers."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.qas.models import QA, QAAnswer, QAStatus


def list_qas(db: Session, *, offset: int, limit: int) -> tuple[list[QA], int]:
    """Return every family QA in stable newest-first order with answers loaded."""

    statement = (
        select(QA)
        .options(
            joinedload(QA.asker),
            selectinload(QA.answers).joinedload(QAAnswer.author),
        )
        .order_by(QA.created_at.desc(), QA.id.desc())
    )
    items = list(db.scalars(statement.offset(offset).limit(limit)).unique())
    total = db.scalar(select(func.count()).select_from(QA))
    return items, int(total or 0)


def list_unanswered_qas(
    db: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[list[QA], int]:
    """Return unanswered QAs in stable newest-first order."""

    statement = (
        select(QA)
        .options(
            joinedload(QA.asker),
            selectinload(QA.answers).joinedload(QAAnswer.author),
        )
        .where(QA.status == QAStatus.UNANSWERED)
        .order_by(QA.created_at.desc(), QA.id.desc())
    )
    items = list(db.scalars(statement.offset(offset).limit(limit)).unique())
    total = db.scalar(
        select(func.count()).select_from(QA).where(QA.status == QAStatus.UNANSWERED)
    )
    return items, int(total or 0)


def get_qa(db: Session, qa_id: UUID) -> QA | None:
    """Return one QA and all its answers with author relationships."""

    statement = (
        select(QA)
        .options(
            joinedload(QA.asker),
            selectinload(QA.answers).joinedload(QAAnswer.author),
        )
        .where(QA.id == qa_id)
    )
    return db.scalar(statement)


def add_qa(db: Session, qa: QA) -> None:
    """Stage a new QA for the surrounding service transaction."""

    db.add(qa)


def delete_qa(db: Session, qa: QA) -> None:
    """Stage a QA deletion for the surrounding service transaction."""

    db.delete(qa)


def get_qa_answer(db: Session, answer_id: UUID) -> QAAnswer | None:
    """Return one QA answer and its author relationship."""

    statement = (
        select(QAAnswer)
        .options(joinedload(QAAnswer.author))
        .where(QAAnswer.id == answer_id)
    )
    return db.scalar(statement)


def add_qa_answer(db: Session, answer: QAAnswer) -> None:
    """Stage a new QA answer for the surrounding service transaction."""

    db.add(answer)


def delete_qa_answer(db: Session, answer: QAAnswer) -> None:
    """Stage an answer deletion for the surrounding service transaction."""

    db.delete(answer)
