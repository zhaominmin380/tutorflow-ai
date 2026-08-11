from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.lesson_note import (
    LessonNoteCreate,
    LessonNoteResponse,
    LessonNoteUpdate,
)
from app.services.lesson_note_service import (
    LessonNoteConflictError,
    LessonNoteLessonNotFoundError,
    LessonNoteNotFoundError,
    LessonNoteService,
)

router = APIRouter(prefix="/lessons", tags=["Lesson Notes"])
lesson_note_service = LessonNoteService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.post(
    "/{lesson_id}/note",
    response_model=ApiResponse[LessonNoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson note",
    description="Create one lesson note for a lesson owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_lesson_note(
    lesson_id: int,
    payload: LessonNoteCreate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson_note = lesson_note_service.create_note(
            db,
            current_user=current_user,
            lesson_id=lesson_id,
            data=payload.model_dump(),
        )
    except LessonNoteLessonNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LessonNoteConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return {"success": True, "message": "Lesson note created.", "data": lesson_note}


@router.get(
    "/{lesson_id}/note",
    response_model=ApiResponse[LessonNoteResponse],
    summary="Get lesson note",
    description="Return the lesson note for a lesson owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_lesson_note(
    lesson_id: int,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson_note = lesson_note_service.get_note(db, current_user=current_user, lesson_id=lesson_id)
    except (LessonNoteLessonNotFoundError, LessonNoteNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {"success": True, "message": "Lesson note retrieved.", "data": lesson_note}


@router.patch(
    "/{lesson_id}/note",
    response_model=ApiResponse[LessonNoteResponse],
    summary="Update lesson note",
    description="Partially update the note fields for one lesson owned by the current user.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_lesson_note(
    lesson_id: int,
    payload: LessonNoteUpdate,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        lesson_note = lesson_note_service.update_note(
            db,
            current_user=current_user,
            lesson_id=lesson_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except (LessonNoteLessonNotFoundError, LessonNoteNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {"success": True, "message": "Lesson note updated.", "data": lesson_note}
