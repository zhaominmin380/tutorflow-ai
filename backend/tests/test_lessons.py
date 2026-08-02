import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-6"

from app.database import SessionLocal
from app.main import app
from app.models import Lesson
from fastapi.testclient import TestClient


class LessonApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

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

    def create_student(self, token: str, name: str = "Lesson Student") -> dict:
        response = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": name, "school": "North School", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def create_lesson(
        self,
        token: str,
        student_id: int,
        start_time: str = "2026-08-01T09:00:00Z",
        duration_minutes: int = 60,
        status: str | None = None,
        remark: str | None = "Algebra practice",
    ) -> dict:
        payload = {
            "student_id": student_id,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "location": "Online",
            "remark": remark,
        }
        if status is not None:
            payload["status"] = status

        response = self.client.post("/api/v1/lessons", headers=self.auth_headers(token), json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def test_lessons_require_jwt(self) -> None:
        listed = self.client.get("/api/v1/lessons")
        created = self.client.post(
            "/api/v1/lessons",
            json={"student_id": 1, "start_time": "2026-08-01T09:00:00Z", "duration_minutes": 60},
        )

        self.assertEqual(listed.status_code, 401)
        self.assertEqual(created.status_code, 401)

    def test_create_detail_update_and_delete_lesson(self) -> None:
        token = self.register_user("lesson-crud@example.com")
        student = self.create_student(token)
        lesson = self.create_lesson(token, student["id"])

        self.assertEqual(lesson["status"], "scheduled")
        detail = self.client.get(f"/api/v1/lessons/{lesson['id']}", headers=self.auth_headers(token))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["student_id"], student["id"])

        updated = self.client.patch(
            f"/api/v1/lessons/{lesson['id']}",
            headers=self.auth_headers(token),
            json={"start_time": "2026-08-02T10:00:00Z", "duration_minutes": 90, "status": "completed"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["data"]["duration_minutes"], 90)
        self.assertEqual(updated.json()["data"]["status"], "completed")

        forbidden_field = self.client.patch(
            f"/api/v1/lessons/{lesson['id']}",
            headers=self.auth_headers(token),
            json={"student_id": student["id"]},
        )
        self.assertEqual(forbidden_field.status_code, 422)

        deleted = self.client.delete(f"/api/v1/lessons/{lesson['id']}", headers=self.auth_headers(token))
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/lessons/{lesson['id']}", headers=self.auth_headers(token)).status_code, 404)

        db = SessionLocal()
        try:
            stored = db.get(Lesson, lesson["id"])
            self.assertIsNone(stored)
        finally:
            db.close()

    def test_list_filters_search_pagination_date_range_and_student_route(self) -> None:
        token = self.register_user("lesson-query@example.com")
        student = self.create_student(token, "Alice Chen")
        self.create_lesson(token, student["id"], "2026-08-01T09:00:00Z", remark="Algebra review")
        self.create_lesson(
            token,
            student["id"],
            "2026-08-10T09:00:00Z",
            status="completed",
            remark="Geometry review",
        )
        self.create_lesson(token, student["id"], "2026-09-01T09:00:00Z", status="cancelled", remark="Later")

        paged = self.client.get(
            "/api/v1/lessons?page=1&page_size=2&sort=date",
            headers=self.auth_headers(token),
        )
        self.assertEqual(paged.status_code, 200)
        self.assertEqual(paged.json()["data"]["pagination"]["total"], 3)
        self.assertEqual(paged.json()["data"]["pagination"]["total_pages"], 2)

        completed = self.client.get("/api/v1/lessons?status=completed", headers=self.auth_headers(token))
        self.assertEqual(completed.json()["data"]["pagination"]["total"], 1)

        searched = self.client.get("/api/v1/lessons?search=Algebra", headers=self.auth_headers(token))
        self.assertEqual(searched.json()["data"]["pagination"]["total"], 1)

        date_range = self.client.get(
            "/api/v1/lessons?start_date=2026-08-01&end_date=2026-08-31",
            headers=self.auth_headers(token),
        )
        self.assertEqual(date_range.json()["data"]["pagination"]["total"], 2)

        student_filtered = self.client.get(
            f"/api/v1/lessons?student_id={student['id']}",
            headers=self.auth_headers(token),
        )
        self.assertEqual(student_filtered.json()["data"]["pagination"]["total"], 3)

        student_lessons = self.client.get(
            f"/api/v1/students/{student['id']}/lessons",
            headers=self.auth_headers(token),
        )
        self.assertEqual(student_lessons.status_code, 200, student_lessons.text)
        self.assertEqual(student_lessons.json()["data"]["pagination"]["total"], 3)

        openapi = self.client.get("/openapi.json")
        self.assertIn("/api/v1/students/{student_id}/lessons", openapi.json()["paths"])

    def test_ownership_and_validation(self) -> None:
        owner_token = self.register_user("lesson-owner@example.com")
        other_token = self.register_user("lesson-other@example.com")
        owner_student = self.create_student(owner_token)
        owner_lesson = self.create_lesson(owner_token, owner_student["id"])

        foreign_student_create = self.client.post(
            "/api/v1/lessons",
            headers=self.auth_headers(other_token),
            json={"student_id": owner_student["id"], "start_time": "2026-08-01T09:00:00Z", "duration_minutes": 60},
        )
        detail = self.client.get(f"/api/v1/lessons/{owner_lesson['id']}", headers=self.auth_headers(other_token))
        update = self.client.patch(
            f"/api/v1/lessons/{owner_lesson['id']}",
            headers=self.auth_headers(other_token),
            json={"status": "cancelled"},
        )
        deleted = self.client.delete(f"/api/v1/lessons/{owner_lesson['id']}", headers=self.auth_headers(other_token))
        invalid_range = self.client.get(
            "/api/v1/lessons?start_date=2026-09-01&end_date=2026-08-01",
            headers=self.auth_headers(owner_token),
        )
        invalid_duration = self.client.post(
            "/api/v1/lessons",
            headers=self.auth_headers(owner_token),
            json={"student_id": owner_student["id"], "start_time": "2026-08-01T09:00:00Z", "duration_minutes": 0},
        )

        self.assertEqual(foreign_student_create.status_code, 404)
        self.assertEqual(detail.status_code, 404)
        self.assertEqual(update.status_code, 404)
        self.assertEqual(deleted.status_code, 404)
        self.assertEqual(invalid_range.status_code, 422)
        self.assertEqual(invalid_duration.status_code, 422)


if __name__ == "__main__":
    unittest.main()
