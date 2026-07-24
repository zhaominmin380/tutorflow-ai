from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LessonNoteCreate(BaseModel):
    raw_note: str | None = None
    ai_summary: str | None = None
    teacher_note: str | None = None
    parent_feedback: str | None = None


class LessonNoteUpdate(BaseModel):
    raw_note: str | None = None
    ai_summary: str | None = None
    teacher_note: str | None = None
    parent_feedback: str | None = None


class LessonNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    raw_note: str | None
    ai_summary: str | None
    teacher_note: str | None
    parent_feedback: str | None
    created_at: datetime
    updated_at: datetime
