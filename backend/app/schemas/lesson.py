from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import LessonStatus
from app.schemas.common import ListResponse


class LessonCreate(BaseModel):
    student_id: int = Field(gt=0)
    start_time: datetime
    duration_minutes: int = Field(gt=0)
    status: LessonStatus = LessonStatus.SCHEDULED
    location: str | None = Field(default=None, max_length=255)
    remark: str | None = None


class LessonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    status: LessonStatus | None = None


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    start_time: datetime
    duration_minutes: int
    status: LessonStatus
    location: str | None
    remark: str | None
    created_at: datetime
    updated_at: datetime


class LessonListResponse(ListResponse[LessonResponse]):
    pass
