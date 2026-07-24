from fastapi import APIRouter

from app.api.v1._samples import SAMPLE_DASHBOARD
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.dashboard import DashboardResponse


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=ApiResponse[DashboardResponse],
    summary="Get dashboard",
    description="Return dashboard counters for lessons, monthly income, students, and unpaid payments.",
    responses={401: {"model": ErrorResponse}},
)
def get_dashboard():
    return {"success": True, "message": "Dashboard retrieved.", "data": SAMPLE_DASHBOARD}
