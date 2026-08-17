from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import PaymentStatus, User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.payment import (
    MonthlyPaymentStatistics,
    OutstandingPaymentStatistics,
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    PaymentUpdate,
)
from app.services.payment_service import (
    PaymentConflictError,
    PaymentLessonNotFoundError,
    PaymentNotFoundError,
    PaymentService,
    PaymentValidationError,
)

router = APIRouter(prefix="/payments", tags=["Payments"])
payment_service = PaymentService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)
page_query = Query(1, ge=1)
page_size_query = Query(20, ge=1, le=100)
payment_sort_query = Query("-created_at", pattern="^-?(created_at|paid_at|amount|status)$")
payment_status_query = Query(default=None, alias="status")
payment_month_query = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


def _raise_payment_error(exc: Exception) -> None:
    if isinstance(exc, PaymentNotFoundError | PaymentLessonNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, PaymentConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, PaymentValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    raise exc


@router.get(
    "",
    response_model=ApiResponse[PaymentListResponse],
    summary="List payments",
    description="List the current user's payments with pagination, sorting, and filters.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_payments(
    page: int = page_query,
    page_size: int = page_size_query,
    sort: str = payment_sort_query,
    student_id: int | None = Query(default=None, gt=0),
    payment_status: PaymentStatus | None = payment_status_query,
    month: str | None = payment_month_query,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = payment_service.list_payments(
            db,
            current_user=current_user,
            page=page,
            page_size=page_size,
            sort=sort,
            student_id=student_id,
            payment_status=payment_status,
            month=month,
        )
    except PaymentValidationError as exc:
        _raise_payment_error(exc)
    return {"success": True, "message": "Payments retrieved.", "data": data}


@router.post(
    "",
    response_model=ApiResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create payment",
    description="Create one pending payment for an owned lesson.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_payment(
    payload: PaymentCreate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        payment = payment_service.create_payment(
            db,
            current_user=current_user,
            lesson_id=payload.lesson_id,
            amount=payload.amount,
            note=payload.note,
        )
    except (PaymentLessonNotFoundError, PaymentConflictError) as exc:
        _raise_payment_error(exc)
    return {"success": True, "message": "Payment created.", "data": payment}


@router.get(
    "/statistics/monthly",
    response_model=ApiResponse[MonthlyPaymentStatistics],
    summary="Get monthly payment statistics",
    description="Return paid payment income and count for one Asia/Taipei calendar month.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def monthly_payment_statistics(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = payment_service.monthly_statistics(db, current_user=current_user, month=month)
    except PaymentValidationError as exc:
        _raise_payment_error(exc)
    return {"success": True, "message": "Monthly payment statistics retrieved.", "data": data}


@router.get(
    "/statistics/outstanding",
    response_model=ApiResponse[OutstandingPaymentStatistics],
    summary="Get outstanding payments",
    description="Return pending payment amount and count for the current user.",
    responses={401: {"model": ErrorResponse}},
)
def outstanding_payment_statistics(
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    data = payment_service.outstanding_statistics(db, current_user=current_user)
    return {"success": True, "message": "Outstanding payments retrieved.", "data": data}


@router.get(
    "/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    summary="Get payment",
    description="Return one payment owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_payment(
    payment_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        payment = payment_service.get_payment(db, current_user=current_user, payment_id=payment_id)
    except PaymentNotFoundError as exc:
        _raise_payment_error(exc)
    return {"success": True, "message": "Payment retrieved.", "data": payment}


@router.patch(
    "/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    summary="Update payment",
    description="Update payment fields after validating status transitions and paid_at rules.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        payment = payment_service.update_payment(
            db,
            current_user=current_user,
            payment_id=payment_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except (PaymentNotFoundError, PaymentConflictError, PaymentValidationError) as exc:
        _raise_payment_error(exc)
    return {"success": True, "message": "Payment updated.", "data": payment}


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel payment",
    description="Cancel a pending payment by setting its status to cancelled. Repeated cancellation is idempotent.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def delete_payment(
    payment_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        payment_service.cancel_payment(db, current_user=current_user, payment_id=payment_id)
    except (PaymentNotFoundError, PaymentConflictError) as exc:
        _raise_payment_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
