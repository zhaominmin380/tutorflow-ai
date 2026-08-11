from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai import AISummaryContent


class LessonNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_note: str = Field(min_length=1, max_length=10000)
    ai_summary: AISummaryContent | None = None
    teacher_note: str | None = Field(default=None, max_length=5000)
    parent_feedback: str | None = Field(default=None, max_length=5000)

    @field_validator("raw_note")
    @classmethod
    def raw_note_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("raw_note cannot be blank.")
        return value


class LessonNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_note: str | None = Field(default=None, max_length=10000)
    ai_summary: AISummaryContent | None = None
    teacher_note: str | None = Field(default=None, max_length=5000)
    parent_feedback: str | None = Field(default=None, max_length=5000)

    @field_validator("raw_note")
    @classmethod
    def optional_raw_note_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("raw_note cannot be blank.")
        return value


class LessonNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    raw_note: str | None
    ai_summary: AISummaryContent | None
    teacher_note: str | None
    parent_feedback: str | None
    created_at: datetime
    updated_at: datetime
