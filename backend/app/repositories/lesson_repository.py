from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Lesson, LessonStatus, Student


class LessonRepository:
    def create(self, db: Session, data: dict[str, Any]) -> Lesson:
        lesson = Lesson(**data)
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson

    def get_by_id(self, db: Session, lesson_id: int, user_id: int) -> Lesson | None:
        return (
            db.query(Lesson)
            .join(Student)
            .filter(
                Lesson.id == lesson_id,
                Student.user_id == user_id,
            )
            .first()
        )

    def list(
        self,
        db: Session,
        user_id: int,
        page: int,
        page_size: int,
        search: str | None,
        student_id: int | None,
        lesson_status: LessonStatus | None,
        start_time: datetime | None,
        end_time: datetime | None,
        sort_field: str,
        sort_desc: bool,
    ) -> tuple[list[Lesson], int]:
        query = (
            db.query(Lesson)
            .join(Student)
            .filter(Student.user_id == user_id)
        )

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Student.name.ilike(pattern),
                    Lesson.location.ilike(pattern),
                    Lesson.remark.ilike(pattern),
                )
            )

        if student_id is not None:
            query = query.filter(Lesson.student_id == student_id)

        if lesson_status is not None:
            query = query.filter(Lesson.status == lesson_status)

        if start_time is not None:
            query = query.filter(Lesson.start_time >= start_time)

        if end_time is not None:
            query = query.filter(Lesson.start_time < end_time)

        total = query.with_entities(func.count(Lesson.id)).scalar() or 0
        sort_column = getattr(Lesson, sort_field)
        if sort_desc:
            sort_column = sort_column.desc()

        items = query.order_by(sort_column, Lesson.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update(self, db: Session, lesson: Lesson, data: dict[str, Any]) -> Lesson:
        for field, value in data.items():
            setattr(lesson, field, value)

        db.commit()
        db.refresh(lesson)
        return lesson

    def delete(self, db: Session, lesson: Lesson) -> None:
        db.delete(lesson)
        db.commit()

    def list_by_student(
        self,
        db: Session,
        user_id: int,
        student_id: int,
        page: int,
        page_size: int,
        lesson_status: LessonStatus | None,
        start_time: datetime | None,
        end_time: datetime | None,
        sort_field: str,
        sort_desc: bool,
    ) -> tuple[list[Lesson], int]:
        return self.list(
            db,
            user_id=user_id,
            page=page,
            page_size=page_size,
            search=None,
            student_id=student_id,
            lesson_status=lesson_status,
            start_time=start_time,
            end_time=end_time,
            sort_field=sort_field,
            sort_desc=sort_desc,
        )
