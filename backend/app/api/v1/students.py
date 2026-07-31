from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.student import (
    StudentCreate,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services.student_service import StudentNotFoundError, StudentService

router = APIRouter(prefix="/students", tags=["Students"])
student_service = StudentService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.get(
    "",
    response_model=ApiResponse[StudentListResponse],
    summary="List students",
    description="List current user's students with pagination, sorting, searching, and filters.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at", pattern="^-?(name|created_at)$"),
    search: str | None = None,
    grade: str | None = None,
    subject: str | None = None,
    active: bool | None = None,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    data = student_service.list_students(
        db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        sort=sort,
        search=search,
        grade=grade,
        subject=subject,
        active=active,
    )
    return {"success": True, "message": "Students retrieved.", "data": data}


@router.get(
    "/{student_id}",
    response_model=ApiResponse[StudentResponse],
    summary="Get student",
    description="Return one student owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_student(
    student_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        student = student_service.get_student(db, current_user=current_user, student_id=student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {"success": True, "message": "Student retrieved.", "data": student}


@router.post(
    "",
    response_model=ApiResponse[StudentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create student",
    description="Create a student for the current user.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_student(
    payload: StudentCreate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    student = student_service.create_student(db, current_user=current_user, data=payload.model_dump())
    return {"success": True, "message": "Student created.", "data": student}


@router.patch(
    "/{student_id}",
    response_model=ApiResponse[StudentResponse],
    summary="Update student",
    description="Partially update one student owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        student = student_service.update_student(
            db,
            current_user=current_user,
            student_id=student_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {"success": True, "message": "Student updated.", "data": student}


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student",
    description="Soft delete one student owned by the current user by setting is_active to false.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_student(
    student_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        student_service.delete_student(db, current_user=current_user, student_id=student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
