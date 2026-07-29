from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import AuthenticationError, decode_access_token
from app.database import get_db
from app.models import User
from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def authentication_exception(detail: str = "Could not validate credentials.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (AuthenticationError, KeyError, TypeError, ValueError):
        raise authentication_exception()

    user = UserRepository().get_by_id(db, user_id)
    if user is None:
        raise authentication_exception()

    return user
