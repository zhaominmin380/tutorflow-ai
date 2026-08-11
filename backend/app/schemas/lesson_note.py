from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai import AISummaryContent


class LessonNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    raw_note: str = Field(min_length=1, max_length=10000)
    ai_summary: AISummaryContent | None = None
    teacher_note: str | None = Field(default=None, max_length=5000)
    parent_feedback: str | None = Field(default=None, max_length=5000)

    @field_validator("raw_note", "teacher_note", "parent_feedback")
    @classmethod
    def text_fields_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("text fields cannot be blank.")
        return value


class LessonNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    raw_note: str | None = Field(default=None, max_length=10000)
    ai_summary: AISummaryContent | None = None
    teacher_note: str | None = Field(default=None, max_length=5000)
    parent_feedback: str | None = Field(default=None, max_length=5000)

    @field_validator("raw_note", "teacher_note", "parent_feedback")
    @classmethod
    def text_fields_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("text fields cannot be blank.")
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
