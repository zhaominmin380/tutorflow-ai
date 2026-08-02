from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from app.models import Lesson, LessonStatus, Student, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import Pagination


class LessonNotFoundError(Exception):
    pass


class LessonStudentNotFoundError(Exception):
    pass


class LessonValidationError(Exception):
    pass


class LessonService:
    allowed_sort_fields: ClassVar[set[str]] = {"start_time", "created_at", "status"}

    def __init__(
        self,
        lesson_repository: LessonRepository | None = None,
        student_repository: StudentRepository | None = None,
    ) -> None:
        self.lesson_repository = lesson_repository or LessonRepository()
        self.student_repository = student_repository or StudentRepository()

    def create_lesson(self, db: Session, current_user: User, data: dict[str, Any]) -> Lesson:
        self._get_owned_active_student(db, current_user=current_user, student_id=data["student_id"])
        self._validate_duration(data.get("duration_minutes"))
        return self.lesson_repository.create(db, data=data)

    def get_lesson(self, db: Session, current_user: User, lesson_id: int) -> Lesson:
        lesson = self.lesson_repository.get_by_id(db, lesson_id=lesson_id, user_id=current_user.id)
        if lesson is None:
            raise LessonNotFoundError("Lesson not found.")
        return lesson

    def list_lessons(
        self,
        db: Session,
        current_user: User,
        page: int,
        page_size: int,
        sort: str,
        search: str | None = None,
        student_id: int | None = None,
        lesson_status: LessonStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        if student_id is not None:
            self._get_owned_active_student(db, current_user=current_user, student_id=student_id)

        start_time, end_time = self._date_range(start_date, end_date)
        items, total = self.lesson_repository.list(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            search=search.strip() if search else None,
            student_id=student_id,
            lesson_status=lesson_status,
            start_time=start_time,
            end_time=end_time,
            **self._sort_options(sort),
        )
        return self._list_result(items, page, page_size, total)

    def update_lesson(
        self,
        db: Session,
        current_user: User,
        lesson_id: int,
        data: dict[str, Any],
    ) -> Lesson:
        if "duration_minutes" in data:
            self._validate_duration(data["duration_minutes"])
        lesson = self.get_lesson(db, current_user=current_user, lesson_id=lesson_id)
        return self.lesson_repository.update(db, lesson=lesson, data=data)

    def delete_lesson(self, db: Session, current_user: User, lesson_id: int) -> None:
        lesson = self.get_lesson(db, current_user=current_user, lesson_id=lesson_id)
        self.lesson_repository.delete(db, lesson=lesson)

    def list_student_lessons(
        self,
        db: Session,
        current_user: User,
        student_id: int,
        page: int,
        page_size: int,
        sort: str,
        lesson_status: LessonStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        self._get_owned_active_student(db, current_user=current_user, student_id=student_id)
        start_time, end_time = self._date_range(start_date, end_date)
        items, total = self.lesson_repository.list_by_student(
            db,
            user_id=current_user.id,
            student_id=student_id,
            page=page,
            page_size=page_size,
            lesson_status=lesson_status,
            start_time=start_time,
            end_time=end_time,
            **self._sort_options(sort),
        )
        return self._list_result(items, page, page_size, total)

    def _get_owned_active_student(self, db: Session, current_user: User, student_id: int) -> Student:
        student = self.student_repository.get_by_id(db, student_id=student_id, user_id=current_user.id)
        if student is None or not student.is_active:
            raise LessonStudentNotFoundError("Student not found.")
        return student

    @staticmethod
    def _validate_duration(duration_minutes: int | None) -> None:
        if duration_minutes is None or duration_minutes <= 0:
            raise LessonValidationError("Lesson duration must be greater than zero.")

    @staticmethod
    def _date_range(start_date: date | None, end_date: date | None) -> tuple[datetime | None, datetime | None]:
        if start_date and end_date and start_date > end_date:
            raise LessonValidationError("start_date must be on or before end_date.")

        start_time = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
        end_time = (
            datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc) if end_date else None
        )
        return start_time, end_time

    def _sort_options(self, sort: str) -> dict[str, Any]:
        sort_desc = sort.startswith("-")
        sort_field = sort[1:] if sort_desc else sort
        if sort_field == "date":
            sort_field = "start_time"
        if sort_field not in self.allowed_sort_fields:
            sort_field = "start_time"
            sort_desc = True
        return {"sort_field": sort_field, "sort_desc": sort_desc}

    @staticmethod
    def _list_result(items: list[Lesson], page: int, page_size: int, total: int) -> dict[str, object]:
        return {
            "items": items,
            "pagination": Pagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=ceil(total / page_size) if total else 0,
            ),
        }
