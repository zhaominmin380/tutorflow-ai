import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-7"

from app.api.v1 import ai as ai_router
from app.database import SessionLocal
from app.main import app
from app.models import AILog, Lesson
from app.services.ai_provider import (
    AIProviderConfigurationError,
    AIProviderRateLimitError,
    AIProviderResult,
    AIProviderTimeoutError,
)
from app.services.ai_service import AIService
from app.services.prompt_service import PromptService
from fastapi.testclient import TestClient

SUMMARY = {
    "overview": "The student practiced linear equations.",
    "learning_progress": ["Solved one-step equations."],
    "strengths": ["Explained each calculation."],
    "difficulties": ["Needs more practice with negatives."],
    "next_steps": ["Practice two-step equations."],
}


class FakeAIProvider:
    provider_name = "fake"
    model_name = "fake-model"

    def __init__(self, contents: list[str] | None = None, error: Exception | None = None) -> None:
        self.contents = contents or []
        self.error = error
        self.response_schemas: list[dict[str, object] | None] = []

    def generate(self, prompt: str, response_schema: dict[str, object] | None = None) -> AIProviderResult:
        self.response_schemas.append(response_schema)
        if self.error:
            raise self.error
        return AIProviderResult(
            provider=self.provider_name,
            model=self.model_name,
            content=self.contents.pop(0),
            duration_ms=12,
        )


class LessonNoteApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_ai_service = ai_router.ai_service
        self.fake_provider = FakeAIProvider()
        ai_router.ai_service = AIService(ai_provider=self.fake_provider)
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        ai_router.ai_service = self.original_ai_service

    def register_user(self, email: str) -> str:
        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "password123", "name": "Teacher"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]["access_token"]

    @staticmethod
    def auth_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def create_lesson(self, token: str) -> int:
        student = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": "AI Student", "school": "North School", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(student.status_code, 201, student.text)
        lesson = self.client.post(
            "/api/v1/lessons",
            headers=self.auth_headers(token),
            json={
                "student_id": student.json()["data"]["id"],
                "start_time": "2026-08-03T09:00:00Z",
                "duration_minutes": 60,
            },
        )
        self.assertEqual(lesson.status_code, 201, lesson.text)
        return lesson.json()["data"]["id"]

    def create_note(self, token: str, lesson_id: int) -> dict:
        response = self.client.post(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(token),
            json={"raw_note": "Practiced linear equations and checked each step."},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def test_lesson_note_create_detail_update_duplicate_and_ownership(self) -> None:
        owner_token = self.register_user("note-owner@example.com")
        other_token = self.register_user("note-other@example.com")
        lesson_id = self.create_lesson(owner_token)
        note = self.create_note(owner_token, lesson_id)

        self.assertEqual(note["raw_note"], "Practiced linear equations and checked each step.")
        detail = self.client.get(f"/api/v1/lessons/{lesson_id}/note", headers=self.auth_headers(owner_token))
        duplicate = self.client.post(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(owner_token),
            json={"raw_note": "A second note"},
        )
        updated = self.client.patch(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(owner_token),
            json={"teacher_note": "Please keep practicing negatives."},
        )
        foreign = self.client.get(f"/api/v1/lessons/{lesson_id}/note", headers=self.auth_headers(other_token))

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["teacher_note"], "Please keep practicing negatives.")
        self.assertEqual(foreign.status_code, 404)

    def test_lesson_note_rejects_blank_text_fields_and_summary_items(self) -> None:
        token = self.register_user("note-validation@example.com")
        lesson_id = self.create_lesson(token)

        blank_create = self.client.post(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(token),
            json={"raw_note": "A valid note", "teacher_note": "   "},
        )
        self.assertEqual(blank_create.status_code, 422)

        self.create_note(token, lesson_id)
        blank_update = self.client.patch(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(token),
            json={"parent_feedback": "\t"},
        )
        invalid_summary_item = self.client.patch(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(token),
            json={
                "ai_summary": {
                    **SUMMARY,
                    "learning_progress": ["  "],
                }
            },
        )

        self.assertEqual(blank_update.status_code, 422)
        self.assertEqual(invalid_summary_item.status_code, 422)

    def test_ai_drafts_do_not_update_note_and_logs_are_recorded(self) -> None:
        token = self.register_user("note-ai@example.com")
        lesson_id = self.create_lesson(token)
        self.create_note(token, lesson_id)
        self.fake_provider.contents = [json.dumps(SUMMARY), "Great progress today. Keep practicing equations."]

        summary = self.client.post("/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id})
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(summary.json()["data"]["ai_summary"]["overview"], SUMMARY["overview"])
        self.assertIsNotNone(self.fake_provider.response_schemas[0])
        self.assertIn("properties", self.fake_provider.response_schemas[0])

        note_after_draft = self.client.get(f"/api/v1/lessons/{lesson_id}/note", headers=self.auth_headers(token))
        self.assertIsNone(note_after_draft.json()["data"]["ai_summary"])

        saved = self.client.patch(
            f"/api/v1/lessons/{lesson_id}/note",
            headers=self.auth_headers(token),
            json={"ai_summary": summary.json()["data"]["ai_summary"], "teacher_note": "Use short examples."},
        )
        self.assertEqual(saved.status_code, 200, saved.text)

        feedback = self.client.post("/api/v1/ai/feedback", headers=self.auth_headers(token), json={"lesson_id": lesson_id})
        self.assertEqual(feedback.status_code, 200, feedback.text)
        self.assertEqual(feedback.json()["data"]["parent_feedback"], "Great progress today. Keep practicing equations.")

        db = SessionLocal()
        try:
            logs = db.query(AILog).filter(AILog.lesson_id == lesson_id).order_by(AILog.id).all()
            self.assertEqual([log.log_type for log in logs], ["summary", "parent_feedback"])
            self.assertTrue(all(log.status == "succeeded" for log in logs))
        finally:
            db.close()

    def test_ai_validates_source_jwt_and_provider_failures(self) -> None:
        token = self.register_user("note-ai-errors@example.com")
        lesson_id = self.create_lesson(token)

        no_auth = self.client.post("/api/v1/ai/summary", json={"lesson_id": lesson_id})
        missing_note = self.client.post("/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id})
        self.assertEqual(no_auth.status_code, 401)
        self.assertEqual(missing_note.status_code, 409)

        self.create_note(token, lesson_id)
        self.fake_provider.contents = ["not valid json"]
        invalid_output = self.client.post("/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id})
        self.assertEqual(invalid_output.status_code, 502)

        self.fake_provider.error = AIProviderTimeoutError("AI provider request timed out.", provider="fake", model="fake-model")
        timeout = self.client.post("/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id})
        self.assertEqual(timeout.status_code, 504)

        self.fake_provider.error = AIProviderConfigurationError(
            "AI provider is not configured.", provider="fake", model="fake-model"
        )
        configuration_error = self.client.post(
            "/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id}
        )
        self.assertEqual(configuration_error.status_code, 503)

        self.fake_provider.error = AIProviderRateLimitError(
            "AI provider rate limit reached.", provider="fake", model="fake-model"
        )
        rate_limited = self.client.post(
            "/api/v1/ai/summary", headers=self.auth_headers(token), json={"lesson_id": lesson_id}
        )
        self.assertEqual(rate_limited.status_code, 503)

        db = SessionLocal()
        try:
            failed_logs = db.query(AILog).filter(AILog.lesson_id == lesson_id, AILog.status == "failed").all()
            self.assertEqual(len(failed_logs), 4)
        finally:
            db.close()

    def test_prompt_service_returns_versioned_templates(self) -> None:
        token = self.register_user("note-prompt@example.com")
        lesson_id = self.create_lesson(token)
        db = SessionLocal()
        try:
            lesson = db.get(Lesson, lesson_id)
            self.assertIsNotNone(lesson)
            assert lesson is not None

            prompt_service = PromptService()
            summary_prompt, summary_version = prompt_service.build_summary_prompt(
                lesson, lesson.student, "Practiced equations."
            )
            feedback_prompt, feedback_version = prompt_service.build_feedback_prompt(
                lesson, lesson.student, SUMMARY, "Keep feedback encouraging."
            )

            self.assertEqual(summary_version, "sprint-7-summary-v1")
            self.assertIn("Practiced equations.", summary_prompt)
            self.assertIn('"next_steps"', summary_prompt)
            self.assertEqual(feedback_version, "sprint-7-feedback-v1")
            self.assertIn("Keep feedback encouraging.", feedback_prompt)
            self.assertIn(SUMMARY["overview"], feedback_prompt)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
