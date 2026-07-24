from fastapi import APIRouter, Query, Response, status

from app.api.v1._samples import SAMPLE_LESSON, list_data
from app.models import LessonStatus
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.lesson import LessonCreate, LessonListResponse, LessonResponse, LessonUpdate


router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get(
    "",
    response_model=ApiResponse[LessonListResponse],
    summary="List lessons",
    description="List lessons with pagination, sorting, searching, and filters.",
    responses={401: {"model": ErrorResponse}},
)
def list_lessons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at", pattern="^-?(start_time|created_at|status)$"),
    search: str | None = None,
    student_id: int | None = None,
    status: LessonStatus | None = None,
):
    data = list_data(SAMPLE_LESSON)
    data["pagination"]["page"] = page
    data["pagination"]["page_size"] = page_size
    return {"success": True, "message": "Lessons retrieved.", "data": data}


@router.get(
    "/{lesson_id}",
    response_model=ApiResponse[LessonResponse],
    summary="Get lesson",
    description="Return one lesson by id.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_lesson(lesson_id: int):
    return {"success": True, "message": "Lesson retrieved.", "data": {**SAMPLE_LESSON, "id": lesson_id}}


@router.post(
    "",
    response_model=ApiResponse[LessonResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson",
    description="Create a lesson for a student.",
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def create_lesson(payload: LessonCreate):
    data = {**SAMPLE_LESSON, **payload.model_dump(), "id": 1}
    return {"success": True, "message": "Lesson created.", "data": data}


@router.patch(
    "/{lesson_id}",
    response_model=ApiResponse[LessonResponse],
    summary="Update lesson",
    description="Partially update one lesson.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_lesson(lesson_id: int, payload: LessonUpdate):
    data = {**SAMPLE_LESSON, "id": lesson_id, **payload.model_dump(exclude_unset=True)}
    return {"success": True, "message": "Lesson updated.", "data": data}


@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lesson",
    description="Delete one lesson and related note/payment by cascade.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_lesson(lesson_id: int):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
