from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import AuthenticationError, decode_access_token
from app.core.config import settings
from app.database import get_db
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.session_service import SessionService, csrf_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def require_browser_request(request: Request) -> None:
    # A custom header cannot be sent by a cross-origin form. No cross-origin
    # credentialed CORS access is enabled for these same-origin browser routes.
    if request.headers.get("X-TutorFlow-Request") != "1" or request.headers.get("Sec-Fetch-Site") == "cross-site":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Same-origin browser request required.")


def require_csrf(request: Request, token: str) -> None:
    provided = request.headers.get("X-CSRF-Token", "")
    if not hmac.compare_digest(provided.encode(), csrf_token(token).encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")


def authentication_exception(detail: str = "Could not validate credentials.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        cookie = request.cookies.get(settings.session_cookie_name)
        try:
            session = SessionService().authenticate(db, cookie)
        except AuthenticationError:
            raise authentication_exception()
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            require_csrf(request, cookie)
        return session.user

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (AuthenticationError, KeyError, TypeError, ValueError):
        raise authentication_exception()

    user = UserRepository().get_by_id(db, user_id)
    if user is None:
        raise authentication_exception()

    return user
