from fastapi import APIRouter, Query

from app.api.v1._samples import SAMPLE_PAYMENT, list_data
from app.models import PaymentStatus
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.payment import PaymentListResponse, PaymentResponse, PaymentUpdate


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get(
    "",
    response_model=ApiResponse[PaymentListResponse],
    summary="List payments",
    description="List payments with pagination, sorting, searching, and filters.",
    responses={401: {"model": ErrorResponse}},
)
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at", pattern="^-?(created_at|paid_at|amount|status)$"),
    search: str | None = None,
    status: PaymentStatus | None = None,
):
    data = list_data(SAMPLE_PAYMENT)
    data["pagination"]["page"] = page
    data["pagination"]["page_size"] = page_size
    return {"success": True, "message": "Payments retrieved.", "data": data}


@router.patch(
    "/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    summary="Update payment",
    description="Partially update payment amount, status, or paid_at.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_payment(payment_id: int, payload: PaymentUpdate):
    data = {**SAMPLE_PAYMENT, "id": payment_id, **payload.model_dump(exclude_unset=True)}
    return {"success": True, "message": "Payment updated.", "data": data}
