from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import BrowserSession


class SessionRepository:
    def get_by_token_hash(self, db: Session, token_hash: str) -> BrowserSession | None:
        return db.query(BrowserSession).filter_by(token_hash=token_hash).first()

    def create(
        self, db: Session, user_id: int, token_hash: str, created_at: datetime, expires_at: datetime,
    ) -> BrowserSession:
        session = BrowserSession(
            user_id=user_id, token_hash=token_hash, created_at=created_at, expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def revoke(self, db: Session, token_hash: str) -> None:
        db.query(BrowserSession).filter_by(token_hash=token_hash).delete()
        db.commit()

    def purge_expired(self, db: Session, now: datetime) -> None:
        db.query(BrowserSession).filter(BrowserSession.expires_at <= now).delete()
        db.commit()
