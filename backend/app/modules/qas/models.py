"""Database models for Family question threads and multi-perspective answers."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for QA audit fields."""

    return datetime.now(UTC)


class QAStatus(str, Enum):
    """Describe whether a QA thread has received any answer."""

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
    """A Family question topic that accepts answers from any family member."""

    __tablename__ = "qas"
    # noinspection SpellCheckingInspection
    __table_args__ = (
        CheckConstraint(
            "char_length(question) BETWEEN 1 AND 2000 AND char_length(btrim(question)) >= 1",
            name="qa_question_length",
        ),
        Index("ix_qas_status_created_at", "status", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asked_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    question: Mapped[str] = mapped_column(Text)
    is_proxy: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
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
    answers: Mapped[list["QAAnswer"]] = relationship(
        "QAAnswer",
        back_populates="qa",
        cascade="all, delete-orphan",
        order_by="QAAnswer.created_at.asc()",
    )


class QAAnswer(Base):
    """An individual answer or recollection contributed to a question topic."""

    __tablename__ = "qa_answers"
    # noinspection SpellCheckingInspection
    __table_args__ = (
        CheckConstraint(
            "char_length(content) BETWEEN 1 AND 10000 AND char_length(btrim(content)) >= 1",
            name="qa_answer_content_length",
        ),
        Index("ix_qa_answers_qa_created_at", "qa_id", text("created_at ASC"), text("id ASC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    qa_id: Mapped[UUID] = mapped_column(ForeignKey("qas.id", ondelete="CASCADE"))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    content: Mapped[str] = mapped_column(Text)
    is_proxy: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
    )
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

    qa: Mapped[QA] = relationship("QA", back_populates="answers")
    author: Mapped[object] = relationship("User", foreign_keys=[author_id])
