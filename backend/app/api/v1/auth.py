from fastapi import APIRouter, status

from app.api.v1._samples import SAMPLE_USER
from app.schemas.auth import AuthTokenResponse, LoginRequest, RegisterRequest
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserResponse


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=ApiResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a teacher account and return an authentication token.",
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def register(payload: RegisterRequest):
    user = {**SAMPLE_USER, "email": payload.email, "name": payload.name}
    return {
        "success": True,
        "message": "User registered.",
        "data": {"access_token": "contract-token", "token_type": "bearer", "user": user},
    }


@router.post(
    "/login",
    response_model=ApiResponse[AuthTokenResponse],
    summary="Login user",
    description="Authenticate a teacher account and return an authentication token.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def login(payload: LoginRequest):
    user = {**SAMPLE_USER, "email": payload.email}
    return {
        "success": True,
        "message": "User logged in.",
        "data": {"access_token": "contract-token", "token_type": "bearer", "user": user},
    }


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user",
    description="Return the authenticated teacher profile.",
    responses={401: {"model": ErrorResponse}},
)
def get_me():
    return {"success": True, "message": "Current user retrieved.", "data": SAMPLE_USER}
