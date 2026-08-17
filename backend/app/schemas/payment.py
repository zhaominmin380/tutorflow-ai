from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import PaymentStatus
from app.schemas.common import ListResponse

MAX_PAYMENT_AMOUNT = Decimal("99999999.99")
PAYMENT_AMOUNT_QUANTUM = Decimal("0.01")


def _validate_money(value: Decimal) -> Decimal:
    try:
        if value <= 0:
            raise ValueError("Amount must be greater than zero.")
        if value > MAX_PAYMENT_AMOUNT:
            raise ValueError("Amount exceeds the maximum supported precision.")
        if value != value.quantize(PAYMENT_AMOUNT_QUANTUM):
            raise ValueError("Amount cannot have more than two decimal places.")
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid decimal number.") from exc
    return value


def _validate_note(value: str | None) -> str | None:
    if value is not None and not value.strip():
        raise ValueError("Note cannot be blank.")
    return value


def _validate_paid_at(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("paid_at must include a timezone.")
    return value


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    lesson_id: int = Field(gt=0)
    amount: Decimal
    note: str | None = Field(default=None, max_length=5000)

    _amount_validator = field_validator("amount")(_validate_money)
    _note_validator = field_validator("note")(_validate_note)


class PaymentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    amount: Decimal | None = None
    status: PaymentStatus | None = None
    paid_at: datetime | None = None
    note: str | None = Field(default=None, max_length=5000)

    _amount_validator = field_validator("amount")(_validate_money)
    _note_validator = field_validator("note")(_validate_note)
    _paid_at_validator = field_validator("paid_at")(_validate_paid_at)

    @model_validator(mode="after")
    def require_update_field(self) -> PaymentUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one payment field is required.")
        return self


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    lesson_id: int
    amount: Decimal
    status: PaymentStatus
    paid_at: datetime | None
    note: str | None
    created_at: datetime
    updated_at: datetime


class PaymentListResponse(ListResponse[PaymentResponse]):
    pass


class MonthlyPaymentStatistics(BaseModel):
    month: str
    monthly_income: Decimal
    paid_count: int
    currency: str = "TWD"


class OutstandingPaymentStatistics(BaseModel):
    outstanding_amount: Decimal
    outstanding_count: int
    currency: str = "TWD"
