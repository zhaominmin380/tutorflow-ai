import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-8"

from app.main import app
from fastapi.testclient import TestClient


class PaymentApiTest(unittest.TestCase):
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

    def create_lesson(self, token: str, name: str = "Payment Student") -> dict:
        student = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": name, "school": "North School", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(student.status_code, 201, student.text)
        student_data = student.json()["data"]
        lesson = self.client.post(
            "/api/v1/lessons",
            headers=self.auth_headers(token),
            json={
                "student_id": student_data["id"],
                "start_time": "2026-08-01T09:00:00Z",
                "duration_minutes": 60,
            },
        )
        self.assertEqual(lesson.status_code, 201, lesson.text)
        return {"student": student_data, "lesson": lesson.json()["data"]}

    def create_payment(self, token: str, lesson_id: int, amount: str = "1200.00") -> dict:
        response = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(token),
            json={"lesson_id": lesson_id, "amount": amount, "note": "August lesson"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def test_payment_endpoints_require_jwt(self) -> None:
        self.assertEqual(self.client.get("/api/v1/payments").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/payments").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/payments/statistics/outstanding").status_code, 401)

    def test_create_detail_list_duplicate_and_ownership(self) -> None:
        owner_token = self.register_user("payment-owner@example.com")
        other_token = self.register_user("payment-other@example.com")
        resource = self.create_lesson(owner_token)
        payment = self.create_payment(owner_token, resource["lesson"]["id"])

        self.assertEqual(payment["student_id"], resource["student"]["id"])
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(payment["note"], "August lesson")

        detail = self.client.get(
            f"/api/v1/payments/{payment['id']}",
            headers=self.auth_headers(owner_token),
        )
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(detail.json()["data"]["id"], payment["id"])

        listed = self.client.get(
            f"/api/v1/payments?status=pending&student_id={resource['student']['id']}",
            headers=self.auth_headers(owner_token),
        )
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual(listed.json()["data"]["pagination"]["total"], 1)

        duplicate = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(owner_token),
            json={"lesson_id": resource["lesson"]["id"], "amount": "1200.00"},
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.text)

        foreign_detail = self.client.get(
            f"/api/v1/payments/{payment['id']}",
            headers=self.auth_headers(other_token),
        )
        self.assertEqual(foreign_detail.status_code, 404)

    def test_status_transitions_cancel_and_statistics(self) -> None:
        token = self.register_user("payment-flow@example.com")
        first = self.create_lesson(token, "First Student")
        second = self.create_lesson(token, "Second Student")
        pending = self.create_payment(token, first["lesson"]["id"], "1200.00")
        paid_candidate = self.create_payment(token, second["lesson"]["id"], "2400.00")

        missing_paid_at = self.client.patch(
            f"/api/v1/payments/{paid_candidate['id']}",
            headers=self.auth_headers(token),
            json={"status": "paid"},
        )
        self.assertEqual(missing_paid_at.status_code, 422, missing_paid_at.text)

        paid = self.client.patch(
            f"/api/v1/payments/{paid_candidate['id']}",
            headers=self.auth_headers(token),
            json={"status": "paid", "paid_at": "2026-08-15T12:00:00+08:00", "note": "Received"},
        )
        self.assertEqual(paid.status_code, 200, paid.text)
        self.assertEqual(paid.json()["data"]["status"], "paid")

        paid_cancel = self.client.delete(
            f"/api/v1/payments/{paid_candidate['id']}",
            headers=self.auth_headers(token),
        )
        self.assertEqual(paid_cancel.status_code, 409, paid_cancel.text)

        cancelled = self.client.delete(
            f"/api/v1/payments/{pending['id']}",
            headers=self.auth_headers(token),
        )
        self.assertEqual(cancelled.status_code, 204)
        self.assertEqual(
            self.client.delete(
                f"/api/v1/payments/{pending['id']}",
                headers=self.auth_headers(token),
            ).status_code,
            204,
        )

        monthly = self.client.get(
            "/api/v1/payments/statistics/monthly?month=2026-08",
            headers=self.auth_headers(token),
        )
        self.assertEqual(monthly.status_code, 200, monthly.text)
        self.assertEqual(monthly.json()["data"]["monthly_income"], "2400.00")
        self.assertEqual(monthly.json()["data"]["paid_count"], 1)

        outstanding = self.client.get(
            "/api/v1/payments/statistics/outstanding",
            headers=self.auth_headers(token),
        )
        self.assertEqual(outstanding.status_code, 200, outstanding.text)
        self.assertEqual(outstanding.json()["data"]["outstanding_amount"], "0.00")
        self.assertEqual(outstanding.json()["data"]["outstanding_count"], 0)

    def test_payment_validation_and_month_filter(self) -> None:
        token = self.register_user("payment-validation@example.com")
        resource = self.create_lesson(token)

        zero_amount = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(token),
            json={"lesson_id": resource["lesson"]["id"], "amount": "0"},
        )
        self.assertEqual(zero_amount.status_code, 422)

        blank_note = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(token),
            json={"lesson_id": resource["lesson"]["id"], "amount": "100.00", "note": "   "},
        )
        self.assertEqual(blank_note.status_code, 422)

        oversized_precision = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(token),
            json={"lesson_id": resource["lesson"]["id"], "amount": "1E+8"},
        )
        self.assertEqual(oversized_precision.status_code, 422, oversized_precision.text)

        invalid_month = self.client.get(
            "/api/v1/payments?month=2026-8",
            headers=self.auth_headers(token),
        )
        self.assertEqual(invalid_month.status_code, 422)

    def test_payment_openapi_exposes_validation_contract(self) -> None:
        openapi = self.client.get("/openapi.json")
        self.assertEqual(openapi.status_code, 200)
        paths = openapi.json()["paths"]
        self.assertIn("422", paths["/api/v1/payments"]["post"]["responses"])
        monthly_parameters = paths["/api/v1/payments/statistics/monthly"]["get"]["parameters"]
        month_parameter = next(parameter for parameter in monthly_parameters if parameter["name"] == "month")
        self.assertEqual(month_parameter["schema"]["pattern"], r"^\d{4}-(0[1-9]|1[0-2])$")


if __name__ == "__main__":
    unittest.main()
