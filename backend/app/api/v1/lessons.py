from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import LessonStatus, User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.lesson import (
    LessonCreate,
    LessonListResponse,
    LessonResponse,
    LessonUpdate,
)
from app.services.lesson_service import (
    LessonNotFoundError,
    LessonService,
    LessonStudentNotFoundError,
    LessonValidationError,
)

router = APIRouter(prefix="/lessons", tags=["Lessons"])
student_lessons_router = APIRouter(prefix="/students", tags=["Lessons"])
lesson_service = LessonService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)
page_query = Query(1, ge=1)
page_size_query = Query(20, ge=1, le=100)
lesson_sort_query = Query("-start_time", pattern="^-?(date|start_time|created_at|status)$")
student_id_query = Query(default=None, gt=0)
lesson_status_query = Query(default=None, alias="status")


@router.get(
    "",
    response_model=ApiResponse[LessonListResponse],
    summary="List lessons",
    description="List the current user's lessons with pagination, search, filters, and sorting.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_lessons(
    page: int = page_query,
    page_size: int = page_size_query,
    sort: str = lesson_sort_query,
    search: str | None = None,
    student_id: int | None = student_id_query,
    lesson_status: LessonStatus | None = lesson_status_query,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = lesson_service.list_lessons(
            db,
            current_user=current_user,
            page=page,
            page_size=page_size,
            sort=sort,
            search=search,
            student_id=student_id,
            lesson_status=lesson_status,
            start_date=start_date,
            end_date=end_date,
        )
    except LessonStudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LessonValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

    return {"success": True, "message": "Lessons retrieved.", "data": data}


@router.get(
    "/{lesson_id}",
    response_model=ApiResponse[LessonResponse],
    summary="Get lesson",
    description="Return one lesson owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_lesson(
    lesson_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson = lesson_service.get_lesson(db, current_user=current_user, lesson_id=lesson_id)
    except LessonNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {"success": True, "message": "Lesson retrieved.", "data": lesson}


@router.post(
    "",
    response_model=ApiResponse[LessonResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson",
    description="Create a lesson for an active student owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_lesson(
    payload: LessonCreate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson = lesson_service.create_lesson(db, current_user=current_user, data=payload.model_dump())
    except LessonStudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LessonValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

    return {"success": True, "message": "Lesson created.", "data": lesson}


@router.patch(
    "/{lesson_id}",
    response_model=ApiResponse[LessonResponse],
    summary="Update lesson",
    description="Update a lesson's start time, duration, or status.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson = lesson_service.update_lesson(
            db,
            current_user=current_user,
            lesson_id=lesson_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except LessonNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LessonValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

    return {"success": True, "message": "Lesson updated.", "data": lesson}


@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lesson",
    description="Delete one lesson owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_lesson(
    lesson_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson_service.delete_lesson(db, current_user=current_user, lesson_id=lesson_id)
    except LessonNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@student_lessons_router.get(
    "/{student_id}/lessons",
    response_model=ApiResponse[LessonListResponse],
    summary="List student lessons",
    description="List lessons for one active student owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_student_lessons(
    student_id: int,
    page: int = page_query,
    page_size: int = page_size_query,
    sort: str = lesson_sort_query,
    lesson_status: LessonStatus | None = lesson_status_query,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        data = lesson_service.list_student_lessons(
            db,
            current_user=current_user,
            student_id=student_id,
            page=page,
            page_size=page_size,
            sort=sort,
            lesson_status=lesson_status,
            start_date=start_date,
            end_date=end_date,
        )
    except LessonStudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LessonValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

    return {"success": True, "message": "Student lessons retrieved.", "data": data}
