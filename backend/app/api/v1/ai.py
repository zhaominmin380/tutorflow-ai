from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.ai import (
    AIFeedbackRequest,
    AIFeedbackResponse,
    AISummaryRequest,
    AISummaryResponse,
)
from app.schemas.common import ApiResponse, ErrorResponse
from app.services.ai_provider import AIProviderError
from app.services.ai_service import (
    AIInputConflictError,
    AILessonNotFoundError,
    AIService,
)

router = APIRouter(prefix="/ai", tags=["AI"])
ai_service = AIService()
db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.post(
    "/summary",
    response_model=ApiResponse[AISummaryResponse],
    summary="Generate lesson summary draft",
    description="Generate a structured AI summary from an existing lesson note without updating the note.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
)
def generate_summary(
    payload: AISummaryRequest,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        ai_summary = ai_service.generate_summary(db, current_user=current_user, lesson_id=payload.lesson_id)
    except AILessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AIInputConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    return {"success": True, "message": "AI summary generated.", "data": {"ai_summary": ai_summary}}


@router.post(
    "/feedback",
    response_model=ApiResponse[AIFeedbackResponse],
    summary="Generate parent feedback draft",
    description="Generate parent feedback from an existing saved AI summary without updating the note.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
)
def generate_feedback(
    payload: AIFeedbackRequest,
    db: Session = db_dependency,
    current_user: User = current_user_dependency,
):
    try:
        parent_feedback = ai_service.generate_parent_feedback(db, current_user=current_user, lesson_id=payload.lesson_id)
    except AILessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AIInputConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    return {"success": True, "message": "Parent feedback generated.", "data": {"parent_feedback": parent_feedback}}
