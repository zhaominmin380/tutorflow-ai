from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import Base
from app.models import AILog, User
from app.repositories.ai_log_repository import AILogRepository


class AILogRetentionTest(unittest.TestCase):
    def test_delete_older_than_removes_only_expired_logs(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = Session(engine)
        try:
            user = User(email="retention@example.com", password_hash="hash", name="Teacher")
            db.add(user)
            db.flush()
            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    AILog(
                        user_id=user.id,
                        log_type="summary",
                        prompt="old",
                        response="old",
                        created_at=now - timedelta(days=91),
                    ),
                    AILog(
                        user_id=user.id,
                        log_type="summary",
                        prompt="new",
                        response="new",
                        created_at=now - timedelta(days=1),
                    ),
                ]
            )
            db.commit()

            deleted = AILogRepository().delete_older_than(db, now - timedelta(days=90))

            self.assertEqual(deleted, 1)
            remaining = db.query(AILog).all()
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0].prompt, "new")
        finally:
            db.close()
            Base.metadata.drop_all(engine)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
