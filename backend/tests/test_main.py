import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"

from app.database import normalize_database_url
from app.main import app, frontend_response, unhandled_exception_handler
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.testclient import TestClient


class MainAppTest(unittest.TestCase):
    def test_root_health_and_database_health_endpoints(self) -> None:
        with patch.dict(os.environ, {"FRONTEND_DIST": ""}):
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

    def test_production_frontend_serves_static_files_and_spa_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            dist = Path(temporary_directory)
            (dist / "assets").mkdir()
            (dist / "index.html").write_text("<main>TutorFlow</main>", encoding="utf-8")
            (dist / "assets" / "app.js").write_text("console.log('Tova')", encoding="utf-8")

            with patch.dict(os.environ, {"FRONTEND_DIST": str(dist)}):
                root_response = frontend_response()
                spa_response = frontend_response("students")
                asset_response = frontend_response("assets/app.js")

                self.assertIsInstance(root_response, FileResponse)
                self.assertEqual(root_response.path, dist / "index.html")
                self.assertIsInstance(spa_response, FileResponse)
                self.assertEqual(spa_response.path, dist / "index.html")
                self.assertIsInstance(asset_response, FileResponse)
                self.assertEqual(asset_response.path, dist / "assets" / "app.js")
                with self.assertRaises(HTTPException):
                    frontend_response("api/v1/not-a-route")

    def test_railway_postgres_urls_use_the_psycopg_driver(self) -> None:
        self.assertEqual(
            normalize_database_url("postgresql://tutorflow:password@postgres:5432/tutorflow"),
            "postgresql+psycopg://tutorflow:password@postgres:5432/tutorflow",
        )


if __name__ == "__main__":
    unittest.main()
