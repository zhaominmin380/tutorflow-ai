from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Lesson, LessonNote, User
from app.repositories.ai_log_repository import AILogRepository
from app.repositories.lesson_note_repository import LessonNoteRepository
from app.repositories.lesson_repository import LessonRepository
from app.schemas.ai import AISummaryContent
from app.services.ai_provider import (
    AIProvider,
    AIProviderError,
    AIProviderInvalidOutputError,
    AIProviderResult,
    OpenAICompatibleProvider,
)
from app.services.prompt_service import PromptService


class AILessonNotFoundError(Exception):
    pass


class AIInputConflictError(Exception):
    pass


class AIService:
    def __init__(
        self,
        ai_provider: AIProvider | None = None,
        prompt_service: PromptService | None = None,
        ai_log_repository: AILogRepository | None = None,
        lesson_repository: LessonRepository | None = None,
        lesson_note_repository: LessonNoteRepository | None = None,
    ) -> None:
        self.ai_provider = ai_provider or OpenAICompatibleProvider()
        self.prompt_service = prompt_service or PromptService()
        self.ai_log_repository = ai_log_repository or AILogRepository()
        self.lesson_repository = lesson_repository or LessonRepository()
        self.lesson_note_repository = lesson_note_repository or LessonNoteRepository()

    def generate_summary(self, db: Session, current_user: User, lesson_id: int) -> AISummaryContent:
        lesson = self._get_owned_lesson(db, current_user=current_user, lesson_id=lesson_id)
        lesson_note = self._get_note_with_raw_note(db, lesson_id=lesson_id)
        prompt, prompt_version = self.prompt_service.build_summary_prompt(lesson, lesson.student, lesson_note.raw_note)
        result = self._generate(db, current_user, lesson, "summary", prompt, prompt_version, response_schema={})
        try:
            summary = AISummaryContent.model_validate(json.loads(result.content))
        except (json.JSONDecodeError, ValidationError) as exc:
            error = AIProviderInvalidOutputError(
                "AI provider returned an invalid structured summary.",
                provider=result.provider,
                model=result.model,
            )
            self._create_log(
                db,
                user_id=current_user.id,
                lesson_id=lesson.id,
                log_type="summary",
                prompt=prompt,
                prompt_version=prompt_version,
                status="failed",
                provider=result.provider,
                model=result.model,
                duration_ms=result.duration_ms,
                response=result.content,
                error_message=str(error),
            )
            raise error from exc

        self._create_log(
            db,
            user_id=current_user.id,
            lesson_id=lesson.id,
            log_type="summary",
            prompt=prompt,
            prompt_version=prompt_version,
            status="succeeded",
            provider=result.provider,
            model=result.model,
            duration_ms=result.duration_ms,
            response=result.content,
            error_message=None,
        )
        return summary

    def generate_parent_feedback(self, db: Session, current_user: User, lesson_id: int) -> str:
        lesson = self._get_owned_lesson(db, current_user=current_user, lesson_id=lesson_id)
        lesson_note = self._get_note_with_summary(db, lesson_id=lesson_id)
        prompt, prompt_version = self.prompt_service.build_feedback_prompt(
            lesson,
            lesson.student,
            lesson_note.ai_summary,
            lesson_note.teacher_note,
        )
        result = self._generate(db, current_user, lesson, "parent_feedback", prompt, prompt_version)
        parent_feedback = result.content.strip()
        self._create_log(
            db,
            user_id=current_user.id,
            lesson_id=lesson.id,
            log_type="parent_feedback",
            prompt=prompt,
            prompt_version=prompt_version,
            status="succeeded",
            provider=result.provider,
            model=result.model,
            duration_ms=result.duration_ms,
            response=parent_feedback,
            error_message=None,
        )
        return parent_feedback

    def _generate(
        self,
        db: Session,
        current_user: User,
        lesson: Lesson,
        log_type: str,
        prompt: str,
        prompt_version: str,
        response_schema: dict[str, object] | None = None,
    ) -> AIProviderResult:
        try:
            result = self.ai_provider.generate(prompt, response_schema=response_schema)
        except AIProviderError as exc:
            self._create_log(
                db,
                user_id=current_user.id,
                lesson_id=lesson.id,
                log_type=log_type,
                prompt=prompt,
                prompt_version=prompt_version,
                status="failed",
                provider=exc.provider,
                model=exc.model,
                duration_ms=None,
                response="",
                error_message=str(exc),
            )
            raise

        return result

    def _get_owned_lesson(self, db: Session, current_user: User, lesson_id: int) -> Lesson:
        lesson = self.lesson_repository.get_by_id(db, lesson_id=lesson_id, user_id=current_user.id)
        if lesson is None:
            raise AILessonNotFoundError("Lesson not found.")
        return lesson

    def _get_note_with_raw_note(self, db: Session, lesson_id: int) -> LessonNote:
        lesson_note = self.lesson_note_repository.get_by_lesson(db, lesson_id=lesson_id)
        if lesson_note is None or not lesson_note.raw_note:
            raise AIInputConflictError("A lesson note with raw_note is required.")
        return lesson_note

    def _get_note_with_summary(self, db: Session, lesson_id: int) -> LessonNote:
        lesson_note = self.lesson_note_repository.get_by_lesson(db, lesson_id=lesson_id)
        if lesson_note is None or lesson_note.ai_summary is None:
            raise AIInputConflictError("A lesson note with ai_summary is required.")
        return lesson_note

    def _create_log(self, db: Session, **data: Any) -> None:
        self.ai_log_repository.create(db, data=data)
