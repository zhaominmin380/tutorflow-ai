from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    message: str
    detail: str | list[dict[str, object]] | None = None


class Pagination(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ListResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination
