from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Lesson, LessonNote, User
from app.repositories.lesson_note_repository import (
    LessonNoteAlreadyExistsError,
    LessonNoteRepository,
)
from app.repositories.lesson_repository import LessonRepository


class LessonNoteLessonNotFoundError(Exception):
    pass


class LessonNoteNotFoundError(Exception):
    pass


class LessonNoteConflictError(Exception):
    pass


class LessonNoteService:
    def __init__(
        self,
        lesson_note_repository: LessonNoteRepository | None = None,
        lesson_repository: LessonRepository | None = None,
    ) -> None:
        self.lesson_note_repository = lesson_note_repository or LessonNoteRepository()
        self.lesson_repository = lesson_repository or LessonRepository()

    def create_note(self, db: Session, current_user: User, lesson_id: int, data: dict[str, Any]) -> LessonNote:
        self._get_owned_lesson(db, current_user=current_user, lesson_id=lesson_id)
        try:
            return self.lesson_note_repository.create(db, lesson_id=lesson_id, data=data)
        except LessonNoteAlreadyExistsError as exc:
            raise LessonNoteConflictError(str(exc)) from exc

    def get_note(self, db: Session, current_user: User, lesson_id: int) -> LessonNote:
        self._get_owned_lesson(db, current_user=current_user, lesson_id=lesson_id)
        lesson_note = self.lesson_note_repository.get_by_lesson(db, lesson_id=lesson_id)
        if lesson_note is None:
            raise LessonNoteNotFoundError("Lesson note not found.")
        return lesson_note

    def update_note(
        self,
        db: Session,
        current_user: User,
        lesson_id: int,
        data: dict[str, Any],
    ) -> LessonNote:
        lesson_note = self.get_note(db, current_user=current_user, lesson_id=lesson_id)
        return self.lesson_note_repository.update(db, lesson_note=lesson_note, data=data)

    def _get_owned_lesson(self, db: Session, current_user: User, lesson_id: int) -> Lesson:
        lesson = self.lesson_repository.get_by_id(db, lesson_id=lesson_id, user_id=current_user.id)
        if lesson is None:
            raise LessonNoteLessonNotFoundError("Lesson not found.")
        return lesson
