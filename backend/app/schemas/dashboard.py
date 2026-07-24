from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    date: date
    today_lessons_count: int
    month_income: Decimal
    active_students_count: int
    unpaid_payments_count: int
