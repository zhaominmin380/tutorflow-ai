from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import AILog


class AILogRepository:
    def create(self, db: Session, data: dict[str, Any]) -> AILog:
        ai_log = AILog(**data)
        db.add(ai_log)
        db.commit()
        db.refresh(ai_log)
        return ai_log
