from __future__ import annotations

from datetime import datetime
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

    def delete_older_than(self, db: Session, cutoff: datetime) -> int:
        deleted_count = (
            db.query(AILog)
            .filter(AILog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_count
