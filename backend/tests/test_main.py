import os
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class MainAppTest(unittest.TestCase):
    def test_root_health_and_database_health_endpoints(self) -> None:
        with TestClient(app) as client:
            root_response = client.get("/")
            health_response = client.get("/health")
            database_response = client.get("/health/db")

        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(root_response.json(), {"message": "TutorFlow API"})
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json(), {"status": "ok"})
        self.assertEqual(database_response.status_code, 200)
        self.assertEqual(database_response.json(), {"status": "ok", "database": "connected"})


if __name__ == "__main__":
    unittest.main()
