from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import AuthenticationError
from app.dependencies.auth import authentication_exception, get_current_user, require_browser_request, require_csrf
from app.models import User
from app.schemas.auth import AuthTokenResponse, LoginRequest, OAuthTokenResponse, RegisterRequest
from app.schemas.auth import BrowserLoginRequest, BrowserRegisterRequest, BrowserSessionResponse
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService, DuplicateEmailError, InvalidCredentialsError
from app.services.session_service import SessionService, csrf_token, utc_datetime


router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()
session_service = SessionService()


def browser_session_result(db: Session, user: User, remember_me: bool, request: Request, response: Response):
    token, session = session_service.create(db, user, remember_me)
    # Replacing a browser's cookie also revokes its previous session.
    session_service.revoke(db, request.cookies.get(settings.session_cookie_name))
    lifetime_seconds = int((utc_datetime(session.expires_at) - utc_datetime(session.created_at)).total_seconds())
    response.set_cookie(
        settings.session_cookie_name, token,
        max_age=lifetime_seconds if remember_me else None,
        expires=utc_datetime(session.expires_at) if remember_me else None,
        path="/", secure=settings.session_cookie_secure, httponly=True, samesite="strict",
    )
    return {
        "success": True,
        "message": "Browser session created.",
        "data": {"user": user, "csrf_token": csrf_token(token), "expires_at": utc_datetime(session.expires_at)},
    }


@router.post("/session", response_model=ApiResponse[BrowserSessionResponse], dependencies=[Depends(require_browser_request)])
def browser_login(payload: BrowserLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return browser_session_result(db, user, payload.remember_me, request, response)


@router.post(
    "/session/register", response_model=ApiResponse[BrowserSessionResponse],
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_browser_request)],
)
def browser_register(payload: BrowserRegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, email=payload.email, password=payload.password, name=payload.name)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return browser_session_result(db, user, payload.remember_me, request, response)


@router.get("/session", response_model=ApiResponse[BrowserSessionResponse], dependencies=[Depends(require_browser_request)])
def browser_session(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.session_cookie_name)
    try:
        session = session_service.authenticate(db, token)
    except AuthenticationError:
        raise authentication_exception()
    return {
        "success": True, "message": "Browser session restored.",
        "data": {"user": session.user, "csrf_token": csrf_token(token), "expires_at": utc_datetime(session.expires_at)},
    }


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_browser_request)])
def browser_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        require_csrf(request, token)
        session_service.revoke(db, token)
    response.delete_cookie(
        settings.session_cookie_name, path="/", secure=settings.session_cookie_secure, httponly=True, samesite="strict",
    )


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
