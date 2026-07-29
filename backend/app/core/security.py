from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


class AuthenticationError(Exception):
    pass


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_context.verify(plain_password, password_hash)


def create_access_token(user_id: int, email: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.require_secret_key(), algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.require_secret_key(), algorithms=[settings.algorithm])
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    if not payload.get("sub"):
        raise AuthenticationError("Invalid token payload.")

    return payload
