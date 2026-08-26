from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.dashboard import (
    MONTH_PATTERN,
    AIAnalyticsResponse,
    DashboardResponse,
    IncomeAnalyticsResponse,
    LessonAnalyticsResponse,
    StudentAnalyticsResponse,
)
from app.services.dashboard_service import DashboardService, DashboardValidationError

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)
month_query = Query(..., pattern=MONTH_PATTERN)


def _raise_dashboard_error(exc: DashboardValidationError) -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


def _overview_response(db: Session, current_user: User) -> dict[str, object]:
    try:
        data = dashboard_service.get_overview(db, current_user=current_user)
    except DashboardValidationError as exc:
        _raise_dashboard_error(exc)
    return {"success": True, "message": "Dashboard retrieved.", "data": data}


@router.get(
    "",
    response_model=ApiResponse[DashboardResponse],
    summary="Get dashboard overview",
    description="Return current-day, current-month, student, payment, and AI counters for the authenticated tutor.",
    responses={401: {"model": ErrorResponse}},
)
def get_dashboard(
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    return _overview_response(db, current_user)


@router.get(
    "/overview",
    response_model=ApiResponse[DashboardResponse],
    summary="Get dashboard overview",
    description="Return the same backward-compatible overview data as GET /dashboard.",
    responses={401: {"model": ErrorResponse}},
)
def get_dashboard_overview(
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    return _overview_response(db, current_user)


@router.get(
    "/income",
    response_model=ApiResponse[IncomeAnalyticsResponse],
    summary="Get income analytics",
    description="Return paid income totals and a daily chart-ready series for one Asia/Taipei calendar month.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def get_income_analytics(
    month: str = month_query,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = dashboard_service.get_income(db, current_user=current_user, month=month)
    except DashboardValidationError as exc:
        _raise_dashboard_error(exc)
    return {"success": True, "message": "Income analytics retrieved.", "data": data}


@router.get(
    "/students",
    response_model=ApiResponse[StudentAnalyticsResponse],
    summary="Get student analytics",
    description="Return active, inactive, and total student counts for the authenticated tutor.",
    responses={401: {"model": ErrorResponse}},
)
def get_student_analytics(
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    data = dashboard_service.get_students(db, current_user=current_user)
    return {"success": True, "message": "Student analytics retrieved.", "data": data}


@router.get(
    "/lessons",
    response_model=ApiResponse[LessonAnalyticsResponse],
    summary="Get lesson analytics",
    description="Return lesson status totals and a daily chart-ready series for one Asia/Taipei calendar month.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def get_lesson_analytics(
    month: str = month_query,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = dashboard_service.get_lessons(db, current_user=current_user, month=month)
    except DashboardValidationError as exc:
        _raise_dashboard_error(exc)
    return {"success": True, "message": "Lesson analytics retrieved.", "data": data}


@router.get(
    "/ai",
    response_model=ApiResponse[AIAnalyticsResponse],
    summary="Get AI analytics",
    description="Return summary, parent feedback, status, and duration statistics for one Asia/Taipei calendar month.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def get_ai_analytics(
    month: str = month_query,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = dashboard_service.get_ai(db, current_user=current_user, month=month)
    except DashboardValidationError as exc:
        _raise_dashboard_error(exc)
    return {"success": True, "message": "AI analytics retrieved.", "data": data}
