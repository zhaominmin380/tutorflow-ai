from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.auth import AuthTokenResponse, LoginRequest, OAuthTokenResponse, RegisterRequest
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService, DuplicateEmailError, InvalidCredentialsError


router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=ApiResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a teacher account and return an authentication token.",
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, email=payload.email, password=payload.password, name=payload.name)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    login_result = auth_service.create_login_result(user=user)
    return {
        "success": True,
        "message": "User registered.",
        "data": {
            "access_token": login_result.access_token,
            "token_type": login_result.token_type,
            "user": login_result.user,
        },
    }


@router.post(
    "/login",
    response_model=ApiResponse[AuthTokenResponse],
    summary="Login user",
    description="Authenticate a teacher account and return an authentication token.",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        login_result = auth_service.login_user(db, email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return {
        "success": True,
        "message": "User logged in.",
        "data": {
            "access_token": login_result.access_token,
            "token_type": login_result.token_type,
            "user": login_result.user,
        },
    }


@router.post(
    "/token",
    response_model=OAuthTokenResponse,
    include_in_schema=False,
)
def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        login_result = auth_service.login_user(db, email=form_data.username, password=form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return {
        "access_token": login_result.access_token,
        "token_type": login_result.token_type,
    }


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user",
    description="Return the authenticated teacher profile.",
    responses={401: {"model": ErrorResponse}},
)
def get_me(current_user: User = Depends(get_current_user)):
    return {"success": True, "message": "Current user retrieved.", "data": current_user}
