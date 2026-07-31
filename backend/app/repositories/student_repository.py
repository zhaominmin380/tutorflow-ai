from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Student


class StudentRepository:
    def create(self, db: Session, user_id: int, data: dict[str, Any]) -> Student:
        student = Student(user_id=user_id, **data)
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    def get_by_id(self, db: Session, student_id: int, user_id: int) -> Student | None:
        return db.query(Student).filter(Student.id == student_id, Student.user_id == user_id).first()

    def list(
        self,
        db: Session,
        user_id: int,
        page: int,
        page_size: int,
        search: str | None,
        grade: str | None,
        subject: str | None,
        active: bool | None,
        sort_field: str,
        sort_desc: bool,
    ) -> tuple[list[Student], int]:
        query = db.query(Student).filter(Student.user_id == user_id)

        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(Student.name.ilike(pattern), Student.school.ilike(pattern)))

        if grade:
            query = query.filter(Student.grade == grade)

        if subject:
            query = query.filter(Student.subject == subject)

        if active is not None:
            query = query.filter(Student.is_active == active)

        total = query.with_entities(func.count(Student.id)).scalar() or 0
        sort_column = getattr(Student, sort_field)
        if sort_desc:
            sort_column = sort_column.desc()

        items = query.order_by(sort_column).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update(self, db: Session, student: Student, data: dict[str, Any]) -> Student:
        for field, value in data.items():
            setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student

    def soft_delete(self, db: Session, student: Student) -> Student:
        student.is_active = False
        db.commit()
        db.refresh(student)
        return student
