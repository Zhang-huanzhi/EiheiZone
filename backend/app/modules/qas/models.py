"""Database model for one Family question and one current Owner answer."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for QA audit fields."""

    return datetime.now(UTC)


class QAStatus(str, Enum):
    """Describe whether a QA has a complete current answer."""

    UNANSWERED = "unanswered"
    ANSWERED = "answered"


def enum_values(enum_class: type[Enum]) -> list[str]:
    """Persist string enum values instead of Python member names."""

    values: list[str] = []
    for member in enum_class:
        value = member.value
        if not isinstance(value, str):
            raise TypeError("Database enum values must be strings")
        values.append(value)
    return values


class QA(Base):
    """A Family question with at most one current Owner answer."""

    __tablename__ = "qas"
    # noinspection SpellCheckingInspection
    __table_args__ = (
        CheckConstraint(
            "char_length(question) BETWEEN 1 AND 2000 AND char_length(btrim(question)) >= 1",
            name="qa_question_length",
        ),
        CheckConstraint(
            "answer IS NULL OR (char_length(answer) BETWEEN 1 AND 10000 "
            "AND char_length(btrim(answer)) >= 1)",
            name="qa_answer_length",
        ),
        CheckConstraint(
            "(status = 'unanswered' AND answer IS NULL AND answered_by IS NULL "
            "AND answered_at IS NULL) OR "
            "(status = 'answered' AND answer IS NOT NULL AND answered_by IS NOT NULL "
            "AND answered_at IS NOT NULL)",
            name="qa_answer_state_consistency",
        ),
        Index("ix_qas_status_created_at", "status", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asked_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[QAStatus] = mapped_column(
        SqlEnum(
            QAStatus,
            name="qa_status",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=enum_values,
        ),
        default=QAStatus.UNANSWERED,
        server_default=text("'unanswered'"),
    )
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    asker: Mapped[object] = relationship("User", foreign_keys=[asked_by])
    answerer: Mapped[object | None] = relationship("User", foreign_keys=[answered_by])
