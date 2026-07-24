from fastapi import APIRouter, status

from app.schemas.ai import AIFeedbackRequest, AIFeedbackResponse, AISummaryRequest, AISummaryResponse
from app.schemas.common import ApiResponse, ErrorResponse


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/summary",
    response_model=ApiResponse[AISummaryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate lesson summary",
    description="Generate an AI summary from the teacher raw lesson note.",
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def generate_summary(payload: AISummaryRequest):
    return {
        "success": True,
        "message": "AI summary generated.",
        "data": {"ai_summary": f"Summary draft for: {payload.raw_note}"},
    }


@router.post(
    "/feedback",
    response_model=ApiResponse[AIFeedbackResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate parent feedback",
    description="Generate parent-facing feedback from the AI summary and teacher revision.",
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def generate_feedback(payload: AIFeedbackRequest):
    return {
        "success": True,
        "message": "Parent feedback generated.",
        "data": {"parent_feedback": f"Parent feedback draft for: {payload.ai_summary}"},
    }
