from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import ai_settings
from app.database import SessionLocal
from app.repositories.ai_log_repository import AILogRepository


def purge_expired_ai_logs() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=ai_settings.log_retention_days)
    with SessionLocal() as db:
        return AILogRepository().delete_older_than(db, cutoff)


if __name__ == "__main__":
    print(f"Deleted {purge_expired_ai_logs()} expired AI logs.")
