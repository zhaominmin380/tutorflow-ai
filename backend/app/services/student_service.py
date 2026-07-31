from __future__ import annotations

from math import ceil
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from app.models import Student, User
from app.repositories.student_repository import StudentRepository
from app.schemas.common import Pagination


class StudentNotFoundError(Exception):
    pass


class StudentService:
    allowed_sort_fields: ClassVar[set[str]] = {"name", "created_at"}

    def __init__(self, student_repository: StudentRepository | None = None) -> None:
        self.student_repository = student_repository or StudentRepository()

    def create_student(self, db: Session, current_user: User, data: dict[str, Any]) -> Student:
        return self.student_repository.create(db, user_id=current_user.id, data=data)

    def get_student(self, db: Session, current_user: User, student_id: int) -> Student:
        student = self.student_repository.get_by_id(db, student_id=student_id, user_id=current_user.id)
        if student is None:
            raise StudentNotFoundError("Student not found.")

        return student

    def list_students(
        self,
        db: Session,
        current_user: User,
        page: int,
        page_size: int,
        sort: str,
        search: str | None = None,
        grade: str | None = None,
        subject: str | None = None,
        active: bool | None = None,
    ) -> dict[str, object]:
        sort_desc = sort.startswith("-")
        sort_field = sort[1:] if sort_desc else sort
        if sort_field not in self.allowed_sort_fields:
            sort_field = "created_at"
            sort_desc = True

        items, total = self.student_repository.list(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            search=search.strip() if search else None,
            grade=grade,
            subject=subject,
            active=active,
            sort_field=sort_field,
            sort_desc=sort_desc,
        )

        return {
            "items": items,
            "pagination": Pagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=ceil(total / page_size) if total else 0,
            ),
        }

    def update_student(self, db: Session, current_user: User, student_id: int, data: dict[str, Any]) -> Student:
        student = self.get_student(db, current_user=current_user, student_id=student_id)
        return self.student_repository.update(db, student=student, data=data)

    def delete_student(self, db: Session, current_user: User, student_id: int) -> Student:
        student = self.get_student(db, current_user=current_user, student_id=student_id)
        return self.student_repository.soft_delete(db, student=student)
