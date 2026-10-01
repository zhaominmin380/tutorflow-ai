from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import AuthenticationError
from app.models import BrowserSession, User
from app.repositories.session_repository import SessionRepository


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hmac.new(
        settings.require_secret_key().encode(), f"browser-csrf:{token}".encode(), hashlib.sha256,
    ).hexdigest()


def utc_datetime(value: datetime) -> datetime:
    # SQLite returns naive timestamps; PostgreSQL preserves the timezone.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class SessionService:
    def __init__(self) -> None:
        self.repository = SessionRepository()

    def create(self, db: Session, user: User, remember_me: bool) -> tuple[str, BrowserSession]:
        now = datetime.now(timezone.utc)
        lifetime = (
            timedelta(days=settings.session_expire_days)
            if remember_me else timedelta(hours=settings.session_expire_hours)
        )
        if lifetime.total_seconds() <= 0:
            raise RuntimeError("Session lifetime must be positive.")
        self.repository.purge_expired(db, now)
        token = secrets.token_urlsafe(32)
        session = self.repository.create(db, user.id, token_hash(token), now, now + lifetime)
        return token, session

    def authenticate(self, db: Session, token: str | None) -> BrowserSession:
        if not token:
            raise AuthenticationError("Missing session.")
        session = self.repository.get_by_token_hash(db, token_hash(token))
        if session is None or utc_datetime(session.expires_at) <= datetime.now(timezone.utc) or session.user is None:
            raise AuthenticationError("Invalid or expired session.")
        return session

    def revoke(self, db: Session, token: str | None) -> None:
        if token:
            self.repository.revoke(db, token_hash(token))
