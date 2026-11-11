"""multi answer qas with proxy flag

Revision ID: b2c3d4e5f6a7
Revises: a7c8d9e0f1b2
Create Date: 2026-11-11 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a7c8d9e0f1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_proxy to qas, create qa_answers, migrate data, and clean up single answer columns."""

    # 1. Add is_proxy column to qas
    op.add_column(
        "qas",
        sa.Column(
            "is_proxy",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    # 2. Create qa_answers table
    op.create_table(
        "qa_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("qa_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "is_proxy",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
            "char_length(content) BETWEEN 1 AND 10000 AND char_length(btrim(content)) >= 1",
            name=op.f("ck_qa_answers_qa_answer_content_length"),
        ),
        sa.ForeignKeyConstraint(
            ["qa_id"],
            ["qas.id"],
            name=op.f("fk_qa_answers_qa_id_qas"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_qa_answers_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qa_answers")),
    )
    op.create_index(
        "ix_qa_answers_qa_created_at",
        "qa_answers",
        ["qa_id", sa.text("created_at ASC"), sa.text("id ASC")],
        unique=False,
    )

    # 3. Data migration: Migrate existing answers from qas to qa_answers
    op.execute(
        sa.text(
            """
            INSERT INTO qa_answers (id, qa_id, author_id, content, is_proxy, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                id,
                answered_by,
                answer,
                false,
                COALESCE(answered_at, created_at),
                COALESCE(answered_at, updated_at)
            FROM qas
            WHERE answer IS NOT NULL AND answered_by IS NOT NULL;
            """
        )
    )

    # 4. Drop old constraints and columns from qas using raw ALTER TABLE
    op.execute(sa.text("ALTER TABLE qas DROP CONSTRAINT IF EXISTS ck_qas_qa_answer_state_consistency"))
    op.execute(sa.text("ALTER TABLE qas DROP CONSTRAINT IF EXISTS ck_qas_qa_answer_length"))
    op.execute(sa.text("ALTER TABLE qas DROP CONSTRAINT IF EXISTS fk_qas_answered_by_users"))
    op.drop_column("qas", "answer")
    op.drop_column("qas", "answered_by")
    op.drop_column("qas", "answered_at")


def downgrade() -> None:
    """Recreate single-answer columns and backfill latest answer from qa_answers."""

    # 1. Re-add dropped columns
    op.add_column("qas", sa.Column("answer", sa.Text(), nullable=True))
    op.add_column("qas", sa.Column("answered_by", sa.Uuid(), nullable=True))
    op.add_column("qas", sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_qas_answered_by_users",
        "qas",
        "users",
        ["answered_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "qa_answer_length",
        "qas",
        "answer IS NULL OR (char_length(answer) BETWEEN 1 AND 10000 AND char_length(btrim(answer)) >= 1)",
    )

    # 2. Backfill latest answer to qas
    op.execute(
        sa.text(
            """
            UPDATE qas q
            SET
                answer = a.content,
                answered_by = a.author_id,
                answered_at = a.created_at,
                status = 'answered'
            FROM (
                SELECT DISTINCT ON (qa_id) qa_id, content, author_id, created_at
                FROM qa_answers
                ORDER BY qa_id, created_at DESC
            ) a
            WHERE q.id = a.qa_id;
            """
        )
    )
    op.create_check_constraint(
        "qa_answer_state_consistency",
        "qas",
        "(status = 'unanswered' AND answer IS NULL AND answered_by IS NULL AND answered_at IS NULL) OR "
        "(status = 'answered' AND answer IS NOT NULL AND answered_by IS NOT NULL AND answered_at IS NOT NULL)",
    )

    # 3. Drop qa_answers table
    op.drop_index("ix_qa_answers_qa_created_at", table_name="qa_answers")
    op.drop_table("qa_answers")

    # 4. Drop is_proxy from qas
    op.drop_column("qas", "is_proxy")
