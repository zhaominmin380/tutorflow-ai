from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1._samples import SAMPLE_STUDENT, list_data
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.student import StudentCreate, StudentListResponse, StudentResponse, StudentUpdate


router = APIRouter(prefix="/students", tags=["Students"])


@router.get(
    "",
    response_model=ApiResponse[StudentListResponse],
    summary="List students",
    description="List students with pagination, sorting, searching, and filters.",
    responses={401: {"model": ErrorResponse}},
)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at", pattern="^-?(name|created_at)$"),
    search: str | None = None,
    grade: str | None = None,
    subject: str | None = None,
    active: bool | None = None,
    current_user: User = Depends(get_current_user),
):
    data = list_data(SAMPLE_STUDENT)
    data["pagination"]["page"] = page
    data["pagination"]["page_size"] = page_size
    return {"success": True, "message": "Students retrieved.", "data": data}


@router.get(
    "/{student_id}",
    response_model=ApiResponse[StudentResponse],
    summary="Get student",
    description="Return one student by id.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_student(student_id: int):
    return {"success": True, "message": "Student retrieved.", "data": {**SAMPLE_STUDENT, "id": student_id}}


@router.post(
    "",
    response_model=ApiResponse[StudentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create student",
    description="Create a student for the authenticated teacher.",
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_student(payload: StudentCreate):
    data = {**SAMPLE_STUDENT, **payload.model_dump(), "id": 1, "user_id": 1, "is_active": True}
    return {"success": True, "message": "Student created.", "data": data}


@router.patch(
    "/{student_id}",
    response_model=ApiResponse[StudentResponse],
    summary="Update student",
    description="Partially update one student.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_student(student_id: int, payload: StudentUpdate):
    data = {**SAMPLE_STUDENT, "id": student_id, **payload.model_dump(exclude_unset=True)}
    return {"success": True, "message": "Student updated.", "data": data}


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student",
    description="Delete one student and related lessons by cascade.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_student(student_id: int):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
