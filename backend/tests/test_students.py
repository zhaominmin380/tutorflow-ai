import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-5"

from app.database import SessionLocal
from app.main import app
from app.repositories.student_repository import StudentRepository
from fastapi.testclient import TestClient


class StudentApiTest(unittest.TestCase):
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

    def auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def create_student(
        self,
        token: str,
        name: str = "John Chen",
        school: str = "North School",
        grade: str = "8",
        subject: str = "Math",
    ) -> dict:
        response = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={
                "name": name,
                "school": school,
                "grade": grade,
                "subject": subject,
                "note": "Test student",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def test_students_require_jwt(self) -> None:
        response = self.client.get("/api/v1/students")
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            "/api/v1/students",
            json={"name": "John", "school": "A", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(response.status_code, 401)

    def test_create_detail_update_and_soft_delete_student(self) -> None:
        token = self.register_user("student-crud@example.com")
        student = self.create_student(token)

        detail = self.client.get(f"/api/v1/students/{student['id']}", headers=self.auth_headers(token))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["name"], "John Chen")

        updated = self.client.patch(
            f"/api/v1/students/{student['id']}",
            headers=self.auth_headers(token),
            json={"name": "John Updated", "is_active": True},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["name"], "John Updated")

        deleted = self.client.delete(f"/api/v1/students/{student['id']}", headers=self.auth_headers(token))
        self.assertEqual(deleted.status_code, 204)

        db = SessionLocal()
        try:
            stored = StudentRepository().get_by_id(db, student_id=student["id"], user_id=student["user_id"])
            self.assertIsNotNone(stored)
            self.assertFalse(stored.is_active)
        finally:
            db.close()

    def test_list_students_pagination_search_filter_and_sort(self) -> None:
        token = self.register_user("student-query@example.com")
        self.create_student(token, name="Alice Wang", school="East School", grade="7", subject="English")
        self.create_student(token, name="Bob Lin", school="West School", grade="8", subject="Math")
        self.create_student(token, name="Charlie Chen", school="East School", grade="8", subject="Math")

        response = self.client.get(
            "/api/v1/students?page=1&page_size=2&sort=name",
            headers=self.auth_headers(token),
        )
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["data"]["pagination"]["total"], 3)
        self.assertEqual(body["data"]["pagination"]["total_pages"], 2)
        self.assertEqual([item["name"] for item in body["data"]["items"]], ["Alice Wang", "Bob Lin"])

        search = self.client.get("/api/v1/students?search=East", headers=self.auth_headers(token))
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()["data"]["pagination"]["total"], 2)

        filtered = self.client.get("/api/v1/students?grade=8&subject=Math", headers=self.auth_headers(token))
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["data"]["pagination"]["total"], 2)

        inactive_student = self.create_student(token, name="Inactive Student")
        self.client.delete(f"/api/v1/students/{inactive_student['id']}", headers=self.auth_headers(token))
        inactive = self.client.get("/api/v1/students?active=false", headers=self.auth_headers(token))
        self.assertEqual(inactive.status_code, 200)
        self.assertEqual(inactive.json()["data"]["pagination"]["total"], 1)

    def test_user_cannot_access_another_users_student(self) -> None:
        owner_token = self.register_user("student-owner@example.com")
        other_token = self.register_user("student-other@example.com")
        student = self.create_student(owner_token)

        detail = self.client.get(f"/api/v1/students/{student['id']}", headers=self.auth_headers(other_token))
        update = self.client.patch(
            f"/api/v1/students/{student['id']}",
            headers=self.auth_headers(other_token),
            json={"name": "Should Not Work"},
        )
        delete = self.client.delete(f"/api/v1/students/{student['id']}", headers=self.auth_headers(other_token))

        self.assertEqual(detail.status_code, 404)
        self.assertEqual(update.status_code, 404)
        self.assertEqual(delete.status_code, 404)

    def test_student_validation_errors(self) -> None:
        token = self.register_user("student-validation@example.com")

        empty_name = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": "", "school": "A", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(empty_name.status_code, 422)

        invalid_grade = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": "John", "school": "A", "grade": " ", "subject": "Math"},
        )
        self.assertEqual(invalid_grade.status_code, 422)


if __name__ == "__main__":
    unittest.main()
