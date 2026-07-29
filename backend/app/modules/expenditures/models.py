"""Database model for Owner-recorded major expenditures."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CHAR, CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for audit fields."""

    return datetime.now(UTC)


class Expenditure(Base):
    """One major expenditure recorded and managed by an Owner."""

    __tablename__ = "expenditures"
    __table_args__ = (
        CheckConstraint("amount > 0", name="expenditure_amount_positive"),
        CheckConstraint(
            "char_length(category) BETWEEN 1 AND 80 "
            "AND category ~ '[^[:space:]]'",
            name="expenditure_category_length",
        ),
        CheckConstraint(
            "char_length(description) BETWEEN 1 AND 2000 "
            "AND description ~ '[^[:space:]]'",
            name="expenditure_description_length",
        ),
        Index("ix_expenditures_spent_on", text("spent_on DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    spent_on: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(CHAR(3))
    category: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
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

    creator: Mapped[object] = relationship("User")
