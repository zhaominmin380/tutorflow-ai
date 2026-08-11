"""add ai teaching assistant fields

Revision ID: 20260803_0002
Revises: 20260715_0001
Create Date: 2026-08-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260803_0002"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "lesson_notes",
        "ai_summary",
        existing_type=sa.Text(),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using=(
            "CASE WHEN ai_summary IS NULL THEN NULL "
            "ELSE json_build_object("
            "'overview', ai_summary, "
            "'learning_progress', json_build_array(), "
            "'strengths', json_build_array(), "
            "'difficulties', json_build_array(), "
            "'next_steps', json_build_array()"
            ") END"
        ),
    )
    op.add_column("ai_logs", sa.Column("lesson_id", sa.Integer(), nullable=True))
    op.add_column("ai_logs", sa.Column("provider", sa.String(length=100), nullable=True))
    op.add_column("ai_logs", sa.Column("model", sa.String(length=100), nullable=True))
    op.add_column("ai_logs", sa.Column("prompt_version", sa.String(length=50), nullable=True))
    op.add_column(
        "ai_logs",
        sa.Column("status", sa.String(length=20), server_default="succeeded", nullable=False),
    )
    op.add_column("ai_logs", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("ai_logs", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_ai_logs_lesson_id_lessons", "ai_logs", "lessons", ["lesson_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_ai_logs_lesson_id"), "ai_logs", ["lesson_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_logs_lesson_id"), table_name="ai_logs")
    op.drop_constraint("fk_ai_logs_lesson_id_lessons", "ai_logs", type_="foreignkey")
    op.drop_column("ai_logs", "duration_ms")
    op.drop_column("ai_logs", "error_message")
    op.drop_column("ai_logs", "status")
    op.drop_column("ai_logs", "prompt_version")
    op.drop_column("ai_logs", "model")
    op.drop_column("ai_logs", "provider")
    op.drop_column("ai_logs", "lesson_id")
    op.alter_column(
        "lesson_notes",
        "ai_summary",
        existing_type=sa.JSON(),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="ai_summary::text",
    )
