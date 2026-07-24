from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import PaymentStatus
from app.schemas.common import ListResponse


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0)
    status: PaymentStatus | None = None
    paid_at: datetime | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    amount: Decimal
    status: PaymentStatus
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentListResponse(ListResponse[PaymentResponse]):
    pass
