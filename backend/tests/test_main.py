import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"

from app.main import app, unhandled_exception_handler
from fastapi.testclient import TestClient


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

    def test_unhandled_errors_use_unified_response(self) -> None:
        response = asyncio.run(unhandled_exception_handler(None, RuntimeError("secret database detail")))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.body,
            b'{"success":false,"message":"Request failed.","detail":"Internal server error."}',
        )


if __name__ == "__main__":
    unittest.main()
