from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import LessonNote


class LessonNoteAlreadyExistsError(Exception):
    pass


class LessonNoteRepository:
    def create(self, db: Session, lesson_id: int, data: dict[str, Any]) -> LessonNote:
        lesson_note = LessonNote(lesson_id=lesson_id, **data)
        db.add(lesson_note)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise LessonNoteAlreadyExistsError("A lesson note already exists for this lesson.") from exc
        db.refresh(lesson_note)
        return lesson_note

    def get_by_lesson(self, db: Session, lesson_id: int) -> LessonNote | None:
        return db.query(LessonNote).filter(LessonNote.lesson_id == lesson_id).first()

    def update(self, db: Session, lesson_note: LessonNote, data: dict[str, Any]) -> LessonNote:
        for field, value in data.items():
            setattr(lesson_note, field, value)

        db.commit()
        db.refresh(lesson_note)
        return lesson_note
