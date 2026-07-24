from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.models import LessonStatus, PaymentStatus


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)

SAMPLE_USER = {
    "id": 1,
    "email": "teacher@example.com",
    "name": "Demo Teacher",
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_STUDENT = {
    "id": 1,
    "user_id": 1,
    "name": "王小明",
    "school": "Demo Junior High",
    "grade": "G7",
    "subject": "Math",
    "hourly_rate": Decimal("1200.00"),
    "is_active": True,
    "note": "Needs more algebra practice.",
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_LESSON = {
    "id": 1,
    "student_id": 1,
    "start_time": datetime(2026, 7, 23, 19, 0, tzinfo=timezone.utc),
    "duration_minutes": 60,
    "status": LessonStatus.SCHEDULED,
    "location": "Online",
    "remark": "Focus on linear equations.",
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_LESSON_NOTE = {
    "id": 1,
    "lesson_id": 1,
    "raw_note": "Covered linear equations.",
    "ai_summary": "Student practiced solving linear equations.",
    "teacher_note": "Reviewed and adjusted the AI summary.",
    "parent_feedback": "Strong progress today.",
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_PAYMENT = {
    "id": 1,
    "lesson_id": 1,
    "amount": Decimal("1200.00"),
    "status": PaymentStatus.PENDING,
    "paid_at": None,
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_DASHBOARD = {
    "date": date(2026, 7, 23),
    "today_lessons_count": 1,
    "month_income": Decimal("1200.00"),
    "active_students_count": 1,
    "unpaid_payments_count": 1,
}


def list_data(item: dict[str, object]) -> dict[str, object]:
    return {
        "items": [item],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 1,
            "total_pages": 1,
        },
    }
