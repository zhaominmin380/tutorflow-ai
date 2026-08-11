from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AISummaryContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: str = Field(min_length=1, max_length=2000)
    learning_progress: list[str] = Field(default_factory=list, max_length=10)
    strengths: list[str] = Field(default_factory=list, max_length=10)
    difficulties: list[str] = Field(default_factory=list, max_length=10)
    next_steps: list[str] = Field(default_factory=list, max_length=10)


class AISummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lesson_id: int = Field(gt=0)


class AIFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lesson_id: int = Field(gt=0)


class AISummaryResponse(BaseModel):
    ai_summary: AISummaryContent


class AIFeedbackResponse(BaseModel):
    parent_feedback: str = Field(min_length=1, max_length=4000)
