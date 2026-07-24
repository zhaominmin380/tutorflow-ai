"""initial schema

Revision ID: 20260715_0001
Revises:
Create Date: 2026-07-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


lesson_status = sa.Enum(
    "scheduled",
    "completed",
    "cancelled",
    "no_show",
    name="lesson_status",
)
payment_status = sa.Enum(
    "pending",
    "paid",
    "cancelled",
    "refunded",
    name="payment_status",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("school", sa.String(length=100), nullable=True),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=False)

    op.create_table(
        "ai_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("log_type", sa.String(length=50), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_logs_user_id"), "ai_logs", ["user_id"], unique=False)

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", lesson_status, server_default="scheduled", nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lessons_student_id"), "lessons", ["student_id"], unique=False)

    op.create_table(
        "lesson_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("raw_note", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("teacher_note", sa.Text(), nullable=True),
        sa.Column("parent_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lesson_notes_lesson_id"), "lesson_notes", ["lesson_id"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", payment_status, server_default="pending", nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_lesson_id"), "payments", ["lesson_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_lesson_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_lesson_notes_lesson_id"), table_name="lesson_notes")
    op.drop_table("lesson_notes")
    op.drop_index(op.f("ix_lessons_student_id"), table_name="lessons")
    op.drop_table("lessons")
    op.drop_index(op.f("ix_ai_logs_user_id"), table_name="ai_logs")
    op.drop_table("ai_logs")
    op.drop_index(op.f("ix_students_user_id"), table_name="students")
    op.drop_table("students")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    payment_status.drop(op.get_bind(), checkfirst=True)
    lesson_status.drop(op.get_bind(), checkfirst=True)
