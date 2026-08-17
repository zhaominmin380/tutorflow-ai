from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Lesson, Payment, PaymentStatus, Student, User


class PaymentAlreadyExistsError(Exception):
    pass


class PaymentRepository:
    def create(self, db: Session, lesson: Lesson, amount: Decimal, note: str | None) -> Payment:
        payment = Payment(
            student_id=lesson.student_id,
            lesson_id=lesson.id,
            amount=amount,
            status=PaymentStatus.PENDING,
            note=note,
        )
        db.add(payment)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            if self._is_unique_violation(exc):
                raise PaymentAlreadyExistsError("A payment already exists for this lesson.") from exc
            raise
        db.refresh(payment)
        return payment

    def get_by_id(self, db: Session, payment_id: int, user_id: int, for_update: bool = False) -> Payment | None:
        query = (
            db.query(Payment)
            .join(Lesson, Payment.lesson_id == Lesson.id)
            .join(Student, Lesson.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .filter(Payment.id == payment_id, User.id == user_id)
        )
        if for_update:
            query = query.with_for_update()
        return query.first()

    def list(
        self,
        db: Session,
        user_id: int,
        page: int,
        page_size: int,
        student_id: int | None,
        payment_status: PaymentStatus | None,
        month_start: datetime | None,
        month_end: datetime | None,
        sort_field: str,
        sort_desc: bool,
    ) -> tuple[list[Payment], int]:
        query = (
            db.query(Payment)
            .join(Lesson, Payment.lesson_id == Lesson.id)
            .join(Student, Lesson.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .filter(User.id == user_id)
        )

        if student_id is not None:
            query = query.filter(Payment.student_id == student_id)
        if payment_status is not None:
            query = query.filter(Payment.status == payment_status)
        if month_start is not None and month_end is not None:
            reporting_timestamp = case(
                (Payment.status == PaymentStatus.PAID, Payment.paid_at),
                else_=Payment.created_at,
            )
            query = query.filter(reporting_timestamp >= month_start, reporting_timestamp < month_end)

        total = query.with_entities(func.count(Payment.id)).scalar() or 0
        sort_column = getattr(Payment, sort_field)
        if sort_desc:
            sort_column = sort_column.desc()

        items = query.order_by(sort_column, Payment.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update(self, db: Session, payment: Payment, data: dict[str, Any]) -> Payment:
        for field, value in data.items():
            setattr(payment, field, value)
        db.commit()
        db.refresh(payment)
        return payment

    def cancel(self, db: Session, payment: Payment) -> Payment:
        payment.status = PaymentStatus.CANCELLED
        db.commit()
        db.refresh(payment)
        return payment

    def monthly_income(
        self,
        db: Session,
        user_id: int,
        month_start: datetime,
        month_end: datetime,
    ) -> tuple[Decimal, int]:
        amount, count = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0),
                func.count(Payment.id),
            )
            .join(Lesson, Payment.lesson_id == Lesson.id)
            .join(Student, Lesson.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .filter(
                User.id == user_id,
                Payment.status == PaymentStatus.PAID,
                Payment.paid_at >= month_start,
                Payment.paid_at < month_end,
            )
            .one()
        )
        return Decimal(str(amount or 0)).quantize(Decimal("0.01")), int(count or 0)

    def outstanding(self, db: Session, user_id: int) -> tuple[Decimal, int]:
        amount, count = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0),
                func.count(Payment.id),
            )
            .join(Lesson, Payment.lesson_id == Lesson.id)
            .join(Student, Lesson.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .filter(User.id == user_id, Payment.status == PaymentStatus.PENDING)
            .one()
        )
        return Decimal(str(amount or 0)).quantize(Decimal("0.01")), int(count or 0)

    @staticmethod
    def _is_unique_violation(exc: IntegrityError) -> bool:
        sqlstate = getattr(exc.orig, "sqlstate", None)
        if sqlstate == "23505":
            return True
        return "UNIQUE CONSTRAINT FAILED" in str(exc.orig).upper()
