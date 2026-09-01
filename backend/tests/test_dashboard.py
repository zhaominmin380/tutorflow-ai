import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-9"

from app.database import SessionLocal
from app.main import app
from app.models import AILog, User
from app.services.dashboard_service import DashboardService
from fastapi.testclient import TestClient


class DashboardApiTest(unittest.TestCase):
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

    def create_student(self, token: str, name: str) -> dict:
        response = self.client.post(
            "/api/v1/students",
            headers=self.auth_headers(token),
            json={"name": name, "school": "North School", "grade": "8", "subject": "Math"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def create_lesson(self, token: str, student_id: int, start_time: str, lesson_status: str) -> dict:
        response = self.client.post(
            "/api/v1/lessons",
            headers=self.auth_headers(token),
            json={
                "student_id": student_id,
                "start_time": start_time,
                "duration_minutes": 60,
                "status": lesson_status,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def create_payment(self, token: str, lesson_id: int, amount: str) -> dict:
        response = self.client.post(
            "/api/v1/payments",
            headers=self.auth_headers(token),
            json={"lesson_id": lesson_id, "amount": amount},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def add_ai_logs(self, email: str) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).one()
            db.add_all(
                [
                    AILog(
                        user_id=user.id,
                        log_type="summary",
                        status="succeeded",
                        duration_ms=1000,
                        prompt="summary",
                        response="{}",
                        created_at=datetime(2026, 8, 1, 1, 0, tzinfo=timezone.utc),
                    ),
                    AILog(
                        user_id=user.id,
                        log_type="parent_feedback",
                        status="succeeded",
                        duration_ms=2000,
                        prompt="feedback",
                        response="Feedback",
                        created_at=datetime(2026, 8, 2, 1, 0, tzinfo=timezone.utc),
                    ),
                    AILog(
                        user_id=user.id,
                        log_type="summary",
                        status="failed",
                        duration_ms=3000,
                        prompt="summary retry",
                        response="",
                        created_at=datetime(2026, 8, 3, 1, 0, tzinfo=timezone.utc),
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

    def test_dashboard_endpoints_require_jwt(self) -> None:
        endpoints = [
            "/api/v1/dashboard",
            "/api/v1/dashboard/overview",
            "/api/v1/dashboard/income?month=2026-08",
            "/api/v1/dashboard/students",
            "/api/v1/dashboard/lessons?month=2026-08",
            "/api/v1/dashboard/ai?month=2026-08",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(endpoint).status_code, 401)

    def test_empty_database_returns_stable_zero_values(self) -> None:
        token = self.register_user("dashboard-empty@example.com")
        headers = self.auth_headers(token)

        overview = self.client.get("/api/v1/dashboard", headers=headers)
        income = self.client.get("/api/v1/dashboard/income?month=2026-08", headers=headers)
        students = self.client.get("/api/v1/dashboard/students", headers=headers)
        lessons = self.client.get("/api/v1/dashboard/lessons?month=2026-08", headers=headers)
        ai = self.client.get("/api/v1/dashboard/ai?month=2026-08", headers=headers)

        for response in (overview, income, students, lessons, ai):
            self.assertEqual(response.status_code, 200, response.text)

        self.assertEqual(overview.json()["data"]["month_income"], "0.00")
        self.assertEqual(overview.json()["data"]["outstanding_payment_amount"], "0.00")
        self.assertEqual(overview.json()["data"]["unpaid_payments_count"], 0)
        self.assertEqual(income.json()["data"]["total_income"], "0.00")
        self.assertEqual(len(income.json()["data"]["daily_series"]), 31)
        self.assertEqual(students.json()["data"], {"total_students": 0, "active_students": 0, "inactive_students": 0})
        self.assertEqual(lessons.json()["data"]["total_lessons"], 0)
        self.assertEqual(lessons.json()["data"]["by_status"], {"scheduled": 0, "completed": 0, "cancelled": 0, "no_show": 0})
        self.assertEqual(len(lessons.json()["data"]["daily_series"]), 31)
        self.assertEqual(ai.json()["data"]["total_requests"], 0)
        self.assertEqual(ai.json()["data"]["average_duration_ms"], "0.00")

    def test_analytics_aggregate_owned_data_and_preserve_overview_alias(self) -> None:
        owner_email = "dashboard-owner@example.com"
        owner_token = self.register_user(owner_email)
        other_token = self.register_user("dashboard-other@example.com")
        headers = self.auth_headers(owner_token)

        active_student = self.create_student(owner_token, "Active Student")
        inactive_student = self.create_student(owner_token, "Inactive Student")
        deactivated = self.client.patch(
            f"/api/v1/students/{inactive_student['id']}",
            headers=headers,
            json={"is_active": False},
        )
        self.assertEqual(deactivated.status_code, 200, deactivated.text)

        scheduled = self.create_lesson(owner_token, active_student["id"], "2026-08-02T09:00:00+08:00", "scheduled")
        completed = self.create_lesson(owner_token, active_student["id"], "2026-08-10T09:00:00+08:00", "completed")
        cancelled = self.create_lesson(owner_token, active_student["id"], "2026-08-11T09:00:00+08:00", "cancelled")
        no_show = self.create_lesson(owner_token, active_student["id"], "2026-08-12T09:00:00+08:00", "no_show")
        september = self.create_lesson(owner_token, active_student["id"], "2026-09-01T09:00:00+08:00", "completed")

        pending = self.create_payment(owner_token, scheduled["id"], "500.00")
        paid = self.create_payment(owner_token, completed["id"], "1200.00")
        paid_response = self.client.patch(
            f"/api/v1/payments/{paid['id']}",
            headers=headers,
            json={"status": "paid", "paid_at": "2026-08-15T12:00:00+08:00"},
        )
        self.assertEqual(paid_response.status_code, 200, paid_response.text)
        september_payment = self.create_payment(owner_token, september["id"], "800.00")
        september_paid = self.client.patch(
            f"/api/v1/payments/{september_payment['id']}",
            headers=headers,
            json={"status": "paid", "paid_at": "2026-09-01T12:00:00+08:00"},
        )
        self.assertEqual(september_paid.status_code, 200, september_paid.text)

        self.add_ai_logs(owner_email)

        taipei = ZoneInfo("Asia/Taipei")
        with patch.object(
            DashboardService,
            "_today_bounds",
            return_value=(
                datetime(2026, 8, 15, tzinfo=taipei),
                datetime(2026, 8, 16, tzinfo=taipei),
            ),
        ):
            overview = self.client.get("/api/v1/dashboard", headers=headers)
            overview_alias = self.client.get("/api/v1/dashboard/overview", headers=headers)
        income = self.client.get("/api/v1/dashboard/income?month=2026-08", headers=headers)
        students = self.client.get("/api/v1/dashboard/students", headers=headers)
        lessons = self.client.get("/api/v1/dashboard/lessons?month=2026-08", headers=headers)
        ai = self.client.get("/api/v1/dashboard/ai?month=2026-08", headers=headers)

        for response in (overview, overview_alias, income, students, lessons, ai):
            self.assertEqual(response.status_code, 200, response.text)

        self.assertEqual(overview.json()["data"], overview_alias.json()["data"])
        overview_data = overview.json()["data"]
        self.assertEqual(overview_data["month_income"], "1200.00")
        self.assertEqual(overview_data["active_students_count"], 1)
        self.assertEqual(overview_data["unpaid_payments_count"], 1)
        self.assertEqual(overview_data["outstanding_payment_amount"], "500.00")
        self.assertEqual(overview_data["ai_requests_count"], 3)

        income_data = income.json()["data"]
        self.assertEqual(income_data["total_income"], "1200.00")
        self.assertEqual(income_data["paid_count"], 1)
        august_15 = next(item for item in income_data["daily_series"] if item["date"] == "2026-08-15")
        self.assertEqual(august_15, {"date": "2026-08-15", "amount": "1200.00", "paid_count": 1})

        self.assertEqual(
            students.json()["data"],
            {"total_students": 2, "active_students": 1, "inactive_students": 1},
        )

        lessons_data = lessons.json()["data"]
        self.assertEqual(lessons_data["total_lessons"], 4)
        self.assertEqual(
            lessons_data["by_status"],
            {"scheduled": 1, "completed": 1, "cancelled": 1, "no_show": 1},
        )
        august_10 = next(item for item in lessons_data["daily_series"] if item["date"] == "2026-08-10")
        self.assertEqual(august_10["total"], 1)
        self.assertEqual(august_10["completed"], 1)

        self.assertEqual(
            ai.json()["data"],
            {
                "month": "2026-08",
                "total_requests": 3,
                "summary_requests": 2,
                "parent_feedback_requests": 1,
                "succeeded_requests": 2,
                "failed_requests": 1,
                "average_duration_ms": "2000.00",
            },
        )

        foreign_income = self.client.get(
            "/api/v1/dashboard/income?month=2026-08",
            headers=self.auth_headers(other_token),
        )
        self.assertEqual(foreign_income.status_code, 200)
        self.assertEqual(foreign_income.json()["data"]["total_income"], "0.00")
        self.assertEqual(foreign_income.json()["data"]["paid_count"], 0)
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(no_show["status"], "no_show")

    def test_month_validation_and_openapi_contract(self) -> None:
        token = self.register_user("dashboard-contract@example.com")
        headers = self.auth_headers(token)

        missing_month = self.client.get("/api/v1/dashboard/income", headers=headers)
        invalid_month = self.client.get("/api/v1/dashboard/lessons?month=2026-13", headers=headers)
        self.assertEqual(missing_month.status_code, 422)
        self.assertEqual(invalid_month.status_code, 422)

        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]
        for path in (
            "/api/v1/dashboard",
            "/api/v1/dashboard/overview",
            "/api/v1/dashboard/income",
            "/api/v1/dashboard/students",
            "/api/v1/dashboard/lessons",
            "/api/v1/dashboard/ai",
        ):
            self.assertIn(path, paths)
            self.assertIn("security", paths[path]["get"])


if __name__ == "__main__":
    unittest.main()
