from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ListResponse


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    school: str = Field(min_length=1, max_length=100)
    grade: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    note: str | None = None

    @field_validator("name", "school", "grade", "subject")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank.")
        return value


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    school: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    subject: str | None = Field(default=None, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    note: str | None = None

    @field_validator("name", "school", "grade", "subject")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank.")
        return value


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
