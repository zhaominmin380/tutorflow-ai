import os
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class ApiContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def register_user(self, email: str = "contract@example.com") -> str:
        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "password123", "name": "Contract Teacher"},
        )
        return response.json()["data"]["access_token"]

    def test_api_v1_routes_are_registered_in_openapi(self) -> None:
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]

        expected_paths = {
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/students",
            "/api/v1/students/{student_id}",
            "/api/v1/lessons",
            "/api/v1/lessons/{lesson_id}",
            "/api/v1/lessons/{lesson_id}/note",
            "/api/v1/payments",
            "/api/v1/payments/{payment_id}",
            "/api/v1/dashboard",
            "/api/v1/ai/summary",
            "/api/v1/ai/feedback",
        }

        self.assertTrue(expected_paths.issubset(paths.keys()))

    def test_student_list_uses_unified_success_response(self) -> None:
        token = self.register_user()
        response = self.client.get(
            "/api/v1/students?page=1&page_size=20&sort=-created_at",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "Students retrieved.")
        self.assertIn("items", body["data"])
        self.assertEqual(body["data"]["pagination"]["page"], 1)

    def test_create_student_contract(self) -> None:
        token = self.register_user("create-contract@example.com")
        response = self.client.post(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "王小明",
                "school": "Demo Junior High",
                "grade": "G7",
                "subject": "Math",
                "hourly_rate": "1200.00",
                "note": "Needs more algebra practice.",
            },
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["name"], "王小明")
        self.assertIn("created_at", body["data"])

    def test_validation_errors_use_unified_error_response(self) -> None:
        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": "bad-email", "password": "short", "name": ""},
        )

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Validation error.")
        self.assertIn("detail", body)


if __name__ == "__main__":
    unittest.main()
