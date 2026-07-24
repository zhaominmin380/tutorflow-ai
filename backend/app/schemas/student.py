from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ListResponse


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    school: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    subject: str | None = Field(default=None, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    note: str | None = None


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    school: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    subject: str | None = Field(default=None, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    note: str | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    school: str | None
    grade: str | None
    subject: str | None
    hourly_rate: Decimal | None
    is_active: bool
    note: str | None
    created_at: datetime
    updated_at: datetime


class StudentListResponse(ListResponse[StudentResponse]):
    pass
