from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class DashboardResponse(BaseModel):
    date: date
    month: str = Field(pattern=MONTH_PATTERN)
    today_lessons_count: int
    month_income: Decimal
    active_students_count: int
    unpaid_payments_count: int
    outstanding_payment_amount: Decimal
    ai_requests_count: int


class IncomeDailyPoint(BaseModel):
    date: date
    amount: Decimal
    paid_count: int


class IncomeAnalyticsResponse(BaseModel):
    month: str = Field(pattern=MONTH_PATTERN)
    currency: str = "TWD"
    total_income: Decimal
    paid_count: int
    daily_series: list[IncomeDailyPoint]


class StudentAnalyticsResponse(BaseModel):
    total_students: int
    active_students: int
    inactive_students: int


class LessonDailyPoint(BaseModel):
    date: date
    total: int
    scheduled: int
    completed: int
    cancelled: int
    no_show: int


class LessonStatusBreakdown(BaseModel):
    scheduled: int
    completed: int
    cancelled: int
    no_show: int


class LessonAnalyticsResponse(BaseModel):
    month: str = Field(pattern=MONTH_PATTERN)
    total_lessons: int
    by_status: LessonStatusBreakdown
    daily_series: list[LessonDailyPoint]


class AIAnalyticsResponse(BaseModel):
    month: str = Field(pattern=MONTH_PATTERN)
    total_requests: int
    summary_requests: int
    parent_feedback_requests: int
    succeeded_requests: int
    failed_requests: int
    average_duration_ms: Decimal
