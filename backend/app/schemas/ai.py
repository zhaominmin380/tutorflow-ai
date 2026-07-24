from __future__ import annotations

from pydantic import BaseModel, Field


class AISummaryRequest(BaseModel):
    lesson_id: int | None = None
    raw_note: str = Field(min_length=1)


class AIFeedbackRequest(BaseModel):
    lesson_id: int | None = None
    ai_summary: str = Field(min_length=1)
    teacher_note: str | None = None


class AISummaryResponse(BaseModel):
    ai_summary: str


class AIFeedbackResponse(BaseModel):
    parent_feedback: str
