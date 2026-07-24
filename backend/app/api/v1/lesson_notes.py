from fastapi import APIRouter, status

from app.api.v1._samples import SAMPLE_LESSON_NOTE
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.lesson_note import LessonNoteCreate, LessonNoteResponse, LessonNoteUpdate


router = APIRouter(prefix="/lessons", tags=["Lesson Notes"])


@router.post(
    "/{lesson_id}/note",
    response_model=ApiResponse[LessonNoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson note",
    description="Create the note, AI summary, teacher revision, and parent feedback for one lesson.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_lesson_note(lesson_id: int, payload: LessonNoteCreate):
    data = {**SAMPLE_LESSON_NOTE, **payload.model_dump(), "lesson_id": lesson_id}
    return {"success": True, "message": "Lesson note created.", "data": data}


@router.patch(
    "/{lesson_id}/note",
    response_model=ApiResponse[LessonNoteResponse],
    summary="Update lesson note",
    description="Partially update the note fields for one lesson.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_lesson_note(lesson_id: int, payload: LessonNoteUpdate):
    data = {**SAMPLE_LESSON_NOTE, "lesson_id": lesson_id, **payload.model_dump(exclude_unset=True)}
    return {"success": True, "message": "Lesson note updated.", "data": data}
