"""create qas

Revision ID: 5c9db2e6a741
Revises: 89d3f7a41a5b
Create Date: 2026-07-27 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c9db2e6a741"
down_revision: Union[str, Sequence[str], None] = "89d3f7a41a5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the QA table, state checks, relationships, and list index."""

    op.create_table(
        "qas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asked_by", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("answered_by", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "unanswered",
                "answered",
                name="qa_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default=sa.text("'unanswered'"),
            nullable=False,
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
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
            "char_length(question) BETWEEN 1 AND 2000 AND char_length(btrim(question)) >= 1",
            name=op.f("ck_qas_qa_question_length"),
        ),
        sa.CheckConstraint(
            "answer IS NULL OR (char_length(answer) BETWEEN 1 AND 10000 "
            "AND char_length(btrim(answer)) >= 1)",
            name=op.f("ck_qas_qa_answer_length"),
        ),
        sa.CheckConstraint(
            "(status = 'unanswered' AND answer IS NULL AND answered_by IS NULL "
            "AND answered_at IS NULL) OR "
            "(status = 'answered' AND answer IS NOT NULL AND answered_by IS NOT NULL "
            "AND answered_at IS NOT NULL)",
            name=op.f("ck_qas_qa_answer_state_consistency"),
        ),
        sa.ForeignKeyConstraint(
            ["asked_by"],
            ["users.id"],
            name=op.f("fk_qas_asked_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["answered_by"],
            ["users.id"],
            name=op.f("fk_qas_answered_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qas")),
    )
    op.create_index(
        "ix_qas_status_created_at",
        "qas",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Remove only the QA table introduced by this migration."""

    op.drop_index("ix_qas_status_created_at", table_name="qas")
    op.drop_table("qas")
