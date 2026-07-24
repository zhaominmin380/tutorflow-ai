import os
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import Base  # noqa: E402
from app.models import AILog, Lesson, LessonNote, LessonStatus, Payment, PaymentStatus, Student, User  # noqa: E402


class ModelRelationshipTest(unittest.TestCase):
    def setUp(self) -> None:
        configure_mappers()
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_user_student_lesson_note_payment_and_ai_log_relationships(self) -> None:
        user = User(
            email="teacher@example.com",
            password_hash="hashed-password",
            name="Teacher",
        )
        student = Student(
            user=user,
            name="Student",
            school="Demo School",
            grade="G7",
            subject="Math",
            hourly_rate=Decimal("1200.00"),
            is_active=True,
            note="Needs more algebra practice.",
        )
        lesson = Lesson(
            student=student,
            start_time=datetime(2026, 7, 15, 19, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            status=LessonStatus.COMPLETED,
            location="Online",
            remark="Focus on algebra practice.",
        )
        LessonNote(
            lesson=lesson,
            raw_note="Covered linear equations.",
            ai_summary="Student practiced solving linear equations.",
            teacher_note="Reviewed and adjusted the AI summary.",
            parent_feedback="Strong progress today.",
        )
        Payment(
            lesson=lesson,
            amount=Decimal("1200.00"),
            status=PaymentStatus.PAID,
        )
        AILog(
            user=user,
            log_type="lesson_summary",
            prompt="Summarize the lesson.",
            response="Student practiced solving linear equations.",
        )

        self.session.add(user)
        self.session.commit()

        saved_user = self.session.query(User).filter_by(email="teacher@example.com").one()

        self.assertEqual(saved_user.students[0].name, "Student")
        self.assertEqual(saved_user.students[0].hourly_rate, Decimal("1200.00"))
        self.assertTrue(saved_user.students[0].is_active)
        self.assertEqual(saved_user.ai_logs[0].log_type, "lesson_summary")
        self.assertEqual(saved_user.students[0].lessons[0].status, LessonStatus.COMPLETED)
        self.assertEqual(saved_user.students[0].lessons[0].duration_minutes, 60)
        self.assertEqual(saved_user.students[0].lessons[0].lesson_note.parent_feedback, "Strong progress today.")
        self.assertEqual(saved_user.students[0].lessons[0].lesson_note.teacher_note, "Reviewed and adjusted the AI summary.")
        self.assertEqual(saved_user.students[0].lessons[0].payment.status, PaymentStatus.PAID)
        self.assertEqual(saved_user.students[0].lessons[0].payment.amount, Decimal("1200.00"))


if __name__ == "__main__":
    unittest.main()
