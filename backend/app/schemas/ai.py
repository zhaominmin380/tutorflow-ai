from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

SummaryItem = Annotated[str, Field(min_length=1, max_length=1000)]


class AISummaryContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    overview: str = Field(min_length=1, max_length=2000)
    learning_progress: list[SummaryItem] = Field(max_length=10)
    strengths: list[SummaryItem] = Field(max_length=10)
    difficulties: list[SummaryItem] = Field(max_length=10)
    next_steps: list[SummaryItem] = Field(max_length=10)


class AISummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lesson_id: int = Field(gt=0)


class AIFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lesson_id: int = Field(gt=0)


class AISummaryResponse(BaseModel):
    ai_summary: AISummaryContent


class AIFeedbackResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    parent_feedback: str = Field(min_length=1, max_length=4000)
