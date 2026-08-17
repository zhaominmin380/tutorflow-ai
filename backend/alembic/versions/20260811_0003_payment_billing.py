"""complete payment and billing domain

Revision ID: 20260811_0003
Revises: 20260803_0002
Create Date: 2026-08-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260811_0003"
down_revision: str | None = "20260803_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("student_id", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("note", sa.Text(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE payments AS p
            SET student_id = l.student_id
            FROM lessons AS l
            WHERE p.lesson_id = l.id
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM payments WHERE student_id IS NULL) THEN
                    RAISE EXCEPTION 'Cannot backfill payments.student_id from lessons';
                END IF;
                IF EXISTS (SELECT 1 FROM payments WHERE amount <= 0) THEN
                    RAISE EXCEPTION 'Cannot add positive payment amount constraint';
                END IF;
                IF EXISTS (SELECT 1 FROM payments WHERE status = 'paid' AND paid_at IS NULL) THEN
                    RAISE EXCEPTION 'Cannot migrate paid payments without paid_at';
                END IF;
            END $$
            """
        )
    )

    op.alter_column("payments", "student_id", nullable=False)
    op.create_foreign_key(
        "fk_payments_student_id_students",
        "payments",
        "students",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_payments_student_id", "payments", ["student_id"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)
    op.create_index("ix_payments_paid_at", "payments", ["paid_at"], unique=False)
    op.create_check_constraint("ck_payments_amount_positive", "payments", "amount > 0")


def downgrade() -> None:
    op.drop_constraint("ck_payments_amount_positive", "payments", type_="check")
    op.drop_index("ix_payments_paid_at", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_student_id", table_name="payments")
    op.drop_constraint("fk_payments_student_id_students", "payments", type_="foreignkey")
    op.drop_column("payments", "note")
    op.drop_column("payments", "student_id")
