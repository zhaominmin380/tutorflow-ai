from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from math import ceil
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import Payment, PaymentStatus, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.payment_repository import (
    PaymentAlreadyExistsError,
    PaymentRepository,
)
from app.schemas.common import Pagination


class PaymentNotFoundError(Exception):
    pass


class PaymentLessonNotFoundError(Exception):
    pass


class PaymentConflictError(Exception):
    pass


class PaymentValidationError(Exception):
    pass


class PaymentService:
    allowed_sort_fields: ClassVar[set[str]] = {"amount", "paid_at", "created_at", "status"}
    reporting_timezone = ZoneInfo("Asia/Taipei")
    max_payment_amount = Decimal("99999999.99")
    payment_amount_quantum = Decimal("0.01")

    def __init__(
        self,
        payment_repository: PaymentRepository | None = None,
        lesson_repository: LessonRepository | None = None,
    ) -> None:
        self.payment_repository = payment_repository or PaymentRepository()
        self.lesson_repository = lesson_repository or LessonRepository()

    def create_payment(
        self,
        db: Session,
        current_user: User,
        lesson_id: int,
        amount: Decimal,
        note: str | None,
    ) -> Payment:
        amount = self._validate_amount(amount)
        note = self._validate_note(note)
        lesson = self.lesson_repository.get_by_id(db, lesson_id=lesson_id, user_id=current_user.id)
        if lesson is None or not lesson.student.is_active:
            raise PaymentLessonNotFoundError("Lesson not found.")

        try:
            return self.payment_repository.create(db, lesson=lesson, amount=amount, note=note)
        except PaymentAlreadyExistsError as exc:
            raise PaymentConflictError(str(exc)) from exc

    def get_payment(self, db: Session, current_user: User, payment_id: int) -> Payment:
        payment = self.payment_repository.get_by_id(db, payment_id=payment_id, user_id=current_user.id)
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")
        return payment

    def list_payments(
        self,
        db: Session,
        current_user: User,
        page: int,
        page_size: int,
        sort: str,
        student_id: int | None = None,
        payment_status: PaymentStatus | None = None,
        month: str | None = None,
    ) -> dict[str, object]:
        month_start, month_end = self._month_bounds(month) if month else (None, None)
        sort_field, sort_desc = self._sort_options(sort)
        items, total = self.payment_repository.list(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            student_id=student_id,
            payment_status=payment_status,
            month_start=month_start,
            month_end=month_end,
            sort_field=sort_field,
            sort_desc=sort_desc,
        )
        return {
            "items": items,
            "pagination": Pagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=ceil(total / page_size) if total else 0,
            ),
        }

    def update_payment(
        self,
        db: Session,
        current_user: User,
        payment_id: int,
        data: dict[str, Any],
    ) -> Payment:
        payment = self.payment_repository.get_by_id(
            db,
            payment_id=payment_id,
            user_id=current_user.id,
            for_update=True,
        )
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")

        self._validate_payment_consistency(payment)
        data = self._validate_update_data(data)
        self._validate_transition(payment, data)
        return self.payment_repository.update(db, payment=payment, data=data)

    def cancel_payment(self, db: Session, current_user: User, payment_id: int) -> Payment:
        payment = self.payment_repository.get_by_id(
            db,
            payment_id=payment_id,
            user_id=current_user.id,
            for_update=True,
        )
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")
        self._validate_payment_consistency(payment)
        if payment.status == PaymentStatus.CANCELLED:
            return payment
        if payment.status in {PaymentStatus.PAID, PaymentStatus.REFUNDED}:
            raise PaymentConflictError("Only pending payments can be cancelled.")
        return self.payment_repository.cancel(db, payment=payment)

    def monthly_statistics(self, db: Session, current_user: User, month: str) -> dict[str, object]:
        month_start, month_end = self._month_bounds(month)
        amount, paid_count = self.payment_repository.monthly_income(
            db,
            user_id=current_user.id,
            month_start=month_start,
            month_end=month_end,
        )
        return {
            "month": month,
            "monthly_income": amount,
            "paid_count": paid_count,
            "currency": "TWD",
        }

    def outstanding_statistics(self, db: Session, current_user: User) -> dict[str, object]:
        amount, outstanding_count = self.payment_repository.outstanding(db, user_id=current_user.id)
        return {
            "outstanding_amount": amount,
            "outstanding_count": outstanding_count,
            "currency": "TWD",
        }

    def _sort_options(self, sort: str) -> tuple[str, bool]:
        sort_desc = sort.startswith("-")
        sort_field = sort[1:] if sort_desc else sort
        if sort_field not in self.allowed_sort_fields:
            raise PaymentValidationError("Invalid payment sort field.")
        return sort_field, sort_desc

    @classmethod
    def _validate_amount(cls, value: Decimal) -> Decimal:
        try:
            amount = Decimal(str(value))
            if amount <= 0:
                raise PaymentValidationError("Amount must be greater than zero.")
            if amount > cls.max_payment_amount:
                raise PaymentValidationError("Amount exceeds the maximum supported precision.")
            if amount != amount.quantize(cls.payment_amount_quantum):
                raise PaymentValidationError("Amount cannot have more than two decimal places.")
        except (InvalidOperation, ValueError) as exc:
            if isinstance(exc, PaymentValidationError):
                raise
            raise PaymentValidationError("Amount must be a valid decimal number.") from exc
        return amount

    @staticmethod
    def _validate_note(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise PaymentValidationError("Note cannot be blank.")
        value = value.strip()
        if len(value) > 5000:
            raise PaymentValidationError("Note cannot exceed 5000 characters.")
        return value

    @classmethod
    def _validate_update_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        validated = dict(data)
        if "amount" in validated:
            validated["amount"] = cls._validate_amount(validated["amount"])
        if "note" in validated:
            validated["note"] = cls._validate_note(validated["note"])
        if "paid_at" in validated:
            validated["paid_at"] = cls._validate_paid_at(validated["paid_at"])
        return validated

    @staticmethod
    def _validate_payment_consistency(payment: Payment) -> None:
        if payment.student_id != payment.lesson.student_id:
            raise PaymentValidationError("Payment student does not match its lesson.")

    @staticmethod
    def _validate_paid_at(value: datetime | None) -> datetime | None:
        if value is not None and (not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None):
            raise PaymentValidationError("paid_at must include a timezone.")
        return value

    @classmethod
    def _month_bounds(cls, month: str) -> tuple[datetime, datetime]:
        if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month) is None:
            raise PaymentValidationError("month must use YYYY-MM format.")
        year, month_number = (int(part) for part in month.split("-"))
        start = datetime(year, month_number, 1, tzinfo=cls.reporting_timezone)
        if month_number == 12:
            end = datetime(year + 1, 1, 1, tzinfo=cls.reporting_timezone)
        else:
            end = datetime(year, month_number + 1, 1, tzinfo=cls.reporting_timezone)
        return start, end

    @staticmethod
    def _validate_transition(payment: Payment, data: dict[str, Any]) -> None:
        current_status = payment.status
        target_status = data.get("status", current_status)

        if current_status == PaymentStatus.REFUNDED or target_status == PaymentStatus.REFUNDED:
            raise PaymentConflictError("Refunded payments cannot be updated in Sprint 8.")

        if current_status == PaymentStatus.PENDING:
            if target_status == PaymentStatus.PAID:
                paid_at = data.get("paid_at")
                if paid_at is None:
                    raise PaymentValidationError("paid_at is required when marking a payment as paid.")
            elif target_status == PaymentStatus.CANCELLED:
                if data.get("paid_at") is not None:
                    raise PaymentConflictError("Cancelled payments cannot have paid_at.")
            elif target_status != PaymentStatus.PENDING:
                raise PaymentConflictError("Payment status transition is not allowed.")
            elif data.get("paid_at") is not None:
                raise PaymentConflictError("Pending payments cannot have paid_at.")
            return

        if current_status == PaymentStatus.PAID:
            if target_status != PaymentStatus.PAID:
                raise PaymentConflictError("Paid payments cannot change status.")
            if "paid_at" in data and data["paid_at"] is None:
                raise PaymentConflictError("Paid payments must have paid_at.")
            return

        if current_status == PaymentStatus.CANCELLED:
            if target_status != PaymentStatus.CANCELLED:
                raise PaymentConflictError("Cancelled payments cannot change status.")
            if data.get("paid_at") is not None:
                raise PaymentConflictError("Cancelled payments cannot have paid_at.")
