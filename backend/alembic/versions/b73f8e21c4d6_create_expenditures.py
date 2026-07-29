"""create expenditures

Revision ID: b73f8e21c4d6
Revises: 5c9db2e6a741
Create Date: 2026-07-28 16:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b73f8e21c4d6"
down_revision: Union[str, Sequence[str], None] = "5c9db2e6a741"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the Expenditure table, integrity checks, and date index."""

    op.create_table(
        "expenditures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("spent_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name=op.f("ck_expenditures_expenditure_amount_positive"),
        ),
        sa.CheckConstraint(
            "char_length(category) BETWEEN 1 AND 80 "
            "AND category ~ '[^[:space:]]'",
            name=op.f("ck_expenditures_expenditure_category_length"),
        ),
        sa.CheckConstraint(
            "char_length(description) BETWEEN 1 AND 2000 "
            "AND description ~ '[^[:space:]]'",
            name=op.f("ck_expenditures_expenditure_description_length"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_expenditures_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expenditures")),
    )
    op.create_index(
        "ix_expenditures_spent_on",
        "expenditures",
        [sa.text("spent_on DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Remove only the Expenditure table introduced by this migration."""

    op.drop_index("ix_expenditures_spent_on", table_name="expenditures")
    op.drop_table("expenditures")
