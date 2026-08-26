from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import LessonStatus, User
from app.repositories.dashboard_repository import DashboardRepository


class DashboardValidationError(Exception):
    pass


class DashboardService:
    reporting_timezone = ZoneInfo("Asia/Taipei")
    month_pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
    lesson_statuses = tuple(status.value for status in LessonStatus)

    def __init__(self, dashboard_repository: DashboardRepository | None = None) -> None:
        self.dashboard_repository = dashboard_repository or DashboardRepository()

    def get_overview(self, db: Session, current_user: User) -> dict[str, object]:
        today_start, tomorrow_start = self._today_bounds()
        month_start, month_end = self._month_bounds(today_start.strftime("%Y-%m"))
        data = self.dashboard_repository.overview(
            db,
            user_id=current_user.id,
            today_start=today_start,
            tomorrow_start=tomorrow_start,
            month_start=month_start,
            month_end=month_end,
        )
        return {
            "date": today_start.date(),
            "month": month_start.strftime("%Y-%m"),
            **data,
        }

    def get_income(self, db: Session, current_user: User, month: str) -> dict[str, object]:
        month_start, month_end = self._month_bounds(month)
        data = self.dashboard_repository.income(
            db,
            user_id=current_user.id,
            month_start=month_start,
            month_end=month_end,
        )
        return {
            "month": month,
            "currency": "TWD",
            "total_income": data["total_income"],
            "paid_count": data["paid_count"],
            "daily_series": self._income_series(month_start, month_end, data["daily_rows"]),
        }

    def get_students(self, db: Session, current_user: User) -> dict[str, int]:
        return self.dashboard_repository.student_statistics(db, user_id=current_user.id)

    def get_lessons(self, db: Session, current_user: User, month: str) -> dict[str, object]:
        month_start, month_end = self._month_bounds(month)
        data = self.dashboard_repository.lesson_statistics(
            db,
            user_id=current_user.id,
            month_start=month_start,
            month_end=month_end,
        )
        by_status = {status: 0 for status in self.lesson_statuses}
        for status, count in data["status_rows"]:
            by_status[self._status_value(status)] = int(count or 0)

        daily_series = self._lesson_series(
            month_start,
            month_end,
            data["daily_rows"],
            data["daily_total_rows"],
        )
        return {
            "month": month,
            "total_lessons": data["total_lessons"],
            "by_status": by_status,
            "daily_series": daily_series,
        }

    def get_ai(self, db: Session, current_user: User, month: str) -> dict[str, object]:
        month_start, month_end = self._month_bounds(month)
        data = self.dashboard_repository.ai_statistics(
            db,
            user_id=current_user.id,
            month_start=month_start,
            month_end=month_end,
        )
        return {"month": month, **data}

    @classmethod
    def _month_bounds(cls, month: str) -> tuple[datetime, datetime]:
        if cls.month_pattern.fullmatch(month) is None:
            raise DashboardValidationError("month must use YYYY-MM format.")

        year, month_number = (int(part) for part in month.split("-"))
        start = datetime(year, month_number, 1, tzinfo=cls.reporting_timezone)
        if month_number == 12:
            end = datetime(year + 1, 1, 1, tzinfo=cls.reporting_timezone)
        else:
            end = datetime(year, month_number + 1, 1, tzinfo=cls.reporting_timezone)
        return start, end

    @classmethod
    def _today_bounds(cls) -> tuple[datetime, datetime]:
        today = datetime.now(cls.reporting_timezone).date()
        start = datetime.combine(today, time.min, tzinfo=cls.reporting_timezone)
        return start, start + timedelta(days=1)

    @classmethod
    def _income_series(
        cls,
        month_start: datetime,
        month_end: datetime,
        rows: list[Any],
    ) -> list[dict[str, object]]:
        values = {
            cls._as_date(row[0]): {
                "amount": cls._money(row[1]),
                "paid_count": int(row[2] or 0),
            }
            for row in rows
        }
        series: list[dict[str, object]] = []
        current = month_start.date()
        while current < month_end.date():
            series.append(
                {
                    "date": current,
                    **values.get(current, {"amount": Decimal("0.00"), "paid_count": 0}),
                }
            )
            current += timedelta(days=1)
        return series

    @classmethod
    def _lesson_series(
        cls,
        month_start: datetime,
        month_end: datetime,
        rows: list[Any],
        total_rows: list[Any],
    ) -> list[dict[str, object]]:
        values: dict[date, dict[str, int]] = {}
        for row in rows:
            day = cls._as_date(row[0])
            status = cls._status_value(row[1])
            values.setdefault(day, {lesson_status: 0 for lesson_status in cls.lesson_statuses})[status] = int(row[2] or 0)
        totals = {cls._as_date(row[0]): int(row[1] or 0) for row in total_rows}

        series: list[dict[str, object]] = []
        current = month_start.date()
        while current < month_end.date():
            counts = values.get(current, {lesson_status: 0 for lesson_status in cls.lesson_statuses})
            series.append(
                {
                    "date": current,
                    "total": totals.get(current, 0),
                    **counts,
                }
            )
            current += timedelta(days=1)
        return series

    @staticmethod
    def _status_value(status: LessonStatus | str) -> str:
        return status.value if isinstance(status, LessonStatus) else str(status)

    @staticmethod
    def _as_date(value: object) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value)[:10])

    @staticmethod
    def _money(value: object) -> Decimal:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
