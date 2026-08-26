from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Date, case, cast, func
from sqlalchemy.orm import Session

from app.models import AILog, Lesson, Payment, PaymentStatus, Student


class DashboardRepository:
    supported_ai_log_types = ("summary", "parent_feedback")

    def overview(
        self,
        db: Session,
        user_id: int,
        today_start: datetime,
        tomorrow_start: datetime,
        month_start: datetime,
        month_end: datetime,
    ) -> dict[str, object]:
        today_lessons_count = (
            db.query(func.count(Lesson.id))
            .join(Student, Lesson.student_id == Student.id)
            .filter(
                Student.user_id == user_id,
                Lesson.start_time >= today_start,
                Lesson.start_time < tomorrow_start,
            )
            .scalar()
            or 0
        )

        month_income, unpaid_count, outstanding_amount = (
            db.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (Payment.status == PaymentStatus.PAID)
                                & (Payment.paid_at >= month_start)
                                & (Payment.paid_at < month_end),
                                Payment.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(case((Payment.status == PaymentStatus.PENDING, 1), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((Payment.status == PaymentStatus.PENDING, Payment.amount), else_=0)),
                    0,
                ),
            )
            .join(Student, Payment.student_id == Student.id)
            .filter(Student.user_id == user_id)
            .one()
        )

        active_students_count = (
            db.query(func.count(Student.id))
            .filter(Student.user_id == user_id, Student.is_active.is_(True))
            .scalar()
            or 0
        )

        ai_requests_count = (
            db.query(func.count(AILog.id))
            .filter(
                AILog.user_id == user_id,
                AILog.log_type.in_(self.supported_ai_log_types),
                AILog.created_at >= month_start,
                AILog.created_at < month_end,
            )
            .scalar()
            or 0
        )

        return {
            "today_lessons_count": int(today_lessons_count),
            "month_income": self._money(month_income),
            "active_students_count": int(active_students_count),
            "unpaid_payments_count": int(unpaid_count or 0),
            "outstanding_payment_amount": self._money(outstanding_amount),
            "ai_requests_count": int(ai_requests_count),
        }

    def income(
        self,
        db: Session,
        user_id: int,
        month_start: datetime,
        month_end: datetime,
    ) -> dict[str, object]:
        total_income, paid_count = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0),
                func.count(Payment.id),
            )
            .join(Student, Payment.student_id == Student.id)
            .filter(
                Student.user_id == user_id,
                Payment.status == PaymentStatus.PAID,
                Payment.paid_at >= month_start,
                Payment.paid_at < month_end,
            )
            .one()
        )

        reporting_date = self._reporting_date_expression(db, Payment.paid_at)
        daily_rows = (
            db.query(
                reporting_date.label("reporting_date"),
                func.coalesce(func.sum(Payment.amount), 0).label("amount"),
                func.count(Payment.id).label("paid_count"),
            )
            .join(Student, Payment.student_id == Student.id)
            .filter(
                Student.user_id == user_id,
                Payment.status == PaymentStatus.PAID,
                Payment.paid_at >= month_start,
                Payment.paid_at < month_end,
            )
            .group_by(reporting_date)
            .order_by(reporting_date)
            .all()
        )

        return {
            "total_income": self._money(total_income),
            "paid_count": int(paid_count or 0),
            "daily_rows": daily_rows,
        }

    def student_statistics(self, db: Session, user_id: int) -> dict[str, int]:
        total_students, active_students = (
            db.query(
                func.count(Student.id),
                func.coalesce(func.sum(case((Student.is_active.is_(True), 1), else_=0)), 0),
            )
            .filter(Student.user_id == user_id)
            .one()
        )
        total = int(total_students or 0)
        active = int(active_students or 0)
        return {
            "total_students": total,
            "active_students": active,
            "inactive_students": total - active,
        }

    def lesson_statistics(
        self,
        db: Session,
        user_id: int,
        month_start: datetime,
        month_end: datetime,
    ) -> dict[str, object]:
        lesson_filter = (
            Student.user_id == user_id,
            Lesson.start_time >= month_start,
            Lesson.start_time < month_end,
        )
        total_lessons = (
            db.query(func.count(Lesson.id))
            .join(Student, Lesson.student_id == Student.id)
            .filter(*lesson_filter)
            .scalar()
            or 0
        )
        status_rows = (
            db.query(Lesson.status, func.count(Lesson.id))
            .join(Student, Lesson.student_id == Student.id)
            .filter(*lesson_filter)
            .group_by(Lesson.status)
            .all()
        )

        reporting_date = self._reporting_date_expression(db, Lesson.start_time)
        daily_rows = (
            db.query(
                reporting_date.label("reporting_date"),
                Lesson.status,
                func.count(Lesson.id).label("lesson_count"),
            )
            .join(Student, Lesson.student_id == Student.id)
            .filter(*lesson_filter)
            .group_by(reporting_date, Lesson.status)
            .order_by(reporting_date, Lesson.status)
            .all()
        )

        daily_total_rows = (
            db.query(
                reporting_date.label("reporting_date"),
                func.count(Lesson.id).label("lesson_count"),
            )
            .join(Student, Lesson.student_id == Student.id)
            .filter(*lesson_filter)
            .group_by(reporting_date)
            .order_by(reporting_date)
            .all()
        )

        return {
            "total_lessons": int(total_lessons),
            "status_rows": status_rows,
            "daily_rows": daily_rows,
            "daily_total_rows": daily_total_rows,
        }

    def ai_statistics(
        self,
        db: Session,
        user_id: int,
        month_start: datetime,
        month_end: datetime,
    ) -> dict[str, object]:
        total_requests, summary_requests, parent_feedback_requests, succeeded_requests, failed_requests, average_duration = (
            db.query(
                func.count(AILog.id),
                func.coalesce(func.sum(case((AILog.log_type == "summary", 1), else_=0)), 0),
                func.coalesce(func.sum(case((AILog.log_type == "parent_feedback", 1), else_=0)), 0),
                func.coalesce(func.sum(case((AILog.status == "succeeded", 1), else_=0)), 0),
                func.coalesce(func.sum(case((AILog.status == "failed", 1), else_=0)), 0),
                func.avg(AILog.duration_ms),
            )
            .filter(
                AILog.user_id == user_id,
                AILog.log_type.in_(self.supported_ai_log_types),
                AILog.created_at >= month_start,
                AILog.created_at < month_end,
            )
            .one()
        )

        return {
            "total_requests": int(total_requests or 0),
            "summary_requests": int(summary_requests or 0),
            "parent_feedback_requests": int(parent_feedback_requests or 0),
            "succeeded_requests": int(succeeded_requests or 0),
            "failed_requests": int(failed_requests or 0),
            "average_duration_ms": self._decimal(average_duration),
        }

    @staticmethod
    def _reporting_date_expression(db: Session, column):
        dialect_name = db.get_bind().dialect.name
        if dialect_name == "sqlite":
            return func.date(column, "+8 hours")
        if dialect_name == "postgresql":
            return cast(func.timezone("Asia/Taipei", column), Date)
        return cast(column, Date)

    @staticmethod
    def _decimal(value: object) -> Decimal:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    @classmethod
    def _money(cls, value: object) -> Decimal:
        return cls._decimal(value)
