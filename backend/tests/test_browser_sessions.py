import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"

from alembic.migration import MigrationContext  # noqa: E402
from alembic.operations import Operations  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import BrowserSession, User  # noqa: E402
from app.services.session_service import token_hash, utc_datetime  # noqa: E402


class BrowserSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url="https://testserver", headers={"X-TutorFlow-Request": "1"})
        self.client.__enter__()
        self.email = f"session-{uuid4().hex}@example.com"
        self.credentials = {"email": self.email, "password": "password123"}

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def register(self, remember_me: bool = True):
        response = self.client.post(
            "/api/v1/auth/session/register",
            json={**self.credentials, "name": "Tutor", "remember_me": remember_me},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response

    def test_persistent_cookie_and_hashed_server_storage(self) -> None:
        response = self.register()
        cookie = response.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=strict", cookie)
        if settings.session_cookie_secure:
            self.assertIn("Secure", cookie)
            self.assertTrue(cookie.startswith("__Host-"))
        self.assertIn("Max-Age=2592000", cookie)
        self.assertIn("expires=", cookie)
        self.assertEqual(response.headers["cache-control"], "no-store")
        data = response.json()["data"]
        self.assertNotIn("access_token", data)
        self.assertNotIn("token_hash", data)
        token = self.client.cookies.get(settings.session_cookie_name)
        self.assertNotIn(token, response.text)
        with SessionLocal() as db:
            session = db.query(BrowserSession).filter_by(user_id=data["user"]["id"]).one()
            self.assertEqual(session.token_hash, token_hash(token))
            self.assertNotEqual(session.token_hash, token)
            self.assertEqual(utc_datetime(session.expires_at) - utc_datetime(session.created_at), timedelta(days=30))

    def test_reopening_without_jwt_or_storage_restores_cookie_session(self) -> None:
        data = self.register().json()["data"]
        with TestClient(app, base_url="https://testserver", headers={"X-TutorFlow-Request": "1"}) as reopened:
            reopened.cookies.update(self.client.cookies)
            restored = reopened.get("/api/v1/auth/session")
            self.assertEqual(restored.status_code, 200, restored.text)
            self.assertEqual(restored.json()["data"], data)
            self.assertEqual(reopened.get("/api/v1/students").status_code, 200)
            self.assertEqual(reopened.get("/api/v1/auth/me").json()["data"]["email"], self.email)

    def test_activity_does_not_extend_absolute_monthly_expiry(self) -> None:
        data = self.register().json()["data"]
        for _ in range(2):
            response = self.client.get("/api/v1/auth/session")
            self.assertEqual(response.json()["data"]["expires_at"], data["expires_at"])
            self.assertNotIn("set-cookie", response.headers)

    def test_regular_session_has_eight_hour_limit_and_no_persistent_cookie(self) -> None:
        response = self.register(remember_me=False)
        self.assertNotIn("Max-Age", response.headers["set-cookie"])
        self.assertNotIn("expires=", response.headers["set-cookie"])
        with SessionLocal() as db:
            session = db.query(BrowserSession).filter_by(user_id=response.json()["data"]["user"]["id"]).one()
            self.assertEqual(utc_datetime(session.expires_at) - utc_datetime(session.created_at), timedelta(hours=8))

    def test_cookie_writes_require_session_bound_csrf(self) -> None:
        data = self.register().json()["data"]
        student = {"name": "Student", "school": "School", "grade": "G7", "subject": "Math"}
        self.assertEqual(self.client.post("/api/v1/students", json=student).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/students", json=student, headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        valid = self.client.post("/api/v1/students", json=student, headers={"X-CSRF-Token": data["csrf_token"]})
        self.assertEqual(valid.status_code, 201, valid.text)
        second = self.client.post("/api/v1/auth/session", json=self.credentials).json()["data"]
        self.assertNotEqual(second["csrf_token"], data["csrf_token"])
        self.assertEqual(self.client.post("/api/v1/students", json=student, headers={"X-CSRF-Token": data["csrf_token"]}).status_code, 403)

    def test_login_replaces_and_revokes_previous_cookie_session(self) -> None:
        self.register()
        previous = self.client.cookies.get(settings.session_cookie_name)
        login = self.client.post("/api/v1/auth/session", json=self.credentials)
        self.assertEqual(login.status_code, 200)
        self.assertNotEqual(self.client.cookies.get(settings.session_cookie_name), previous)
        with SessionLocal() as db:
            self.assertIsNone(db.query(BrowserSession).filter_by(token_hash=token_hash(previous)).first())

    def test_logout_revokes_only_this_device_and_prevents_cookie_replay(self) -> None:
        data = self.register().json()["data"]
        stolen_cookie = self.client.cookies.get(settings.session_cookie_name)
        with TestClient(app, base_url="https://testserver", headers={"X-TutorFlow-Request": "1"}) as other_device:
            other_device.post("/api/v1/auth/session", json=self.credentials)
            self.assertEqual(self.client.delete("/api/v1/auth/session").status_code, 403)
            response = self.client.delete("/api/v1/auth/session", headers={"X-CSRF-Token": data["csrf_token"]})
            self.assertEqual(response.status_code, 204, response.text)
            self.assertIn("Max-Age=0", response.headers["set-cookie"])
            self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 401)
            self.client.cookies.set(settings.session_cookie_name, stolen_cookie)
            self.assertEqual(self.client.get("/api/v1/students").status_code, 401)
            self.assertEqual(other_device.get("/api/v1/students").status_code, 200)

    def test_expired_session_rejected_server_side_even_if_cookie_present(self) -> None:
        data = self.register().json()["data"]
        with SessionLocal() as db:
            session = db.query(BrowserSession).filter_by(user_id=data["user"]["id"]).one()
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/students").status_code, 401)

    def test_browser_login_and_registration_reject_cross_site_requests(self) -> None:
        for path, payload in [
            ("/api/v1/auth/session", self.credentials),
            ("/api/v1/auth/session/register", {**self.credentials, "name": "Tutor"}),
        ]:
            self.assertEqual(self.client.post(path, json=payload, headers={"X-TutorFlow-Request": "0"}).status_code, 403)
            self.assertEqual(self.client.post(path, json=payload, headers={"Sec-Fetch-Site": "cross-site"}).status_code, 403)

    def test_invalid_credentials_do_not_replace_existing_session(self) -> None:
        self.register()
        previous = self.client.cookies.get(settings.session_cookie_name)
        response = self.client.post("/api/v1/auth/session", json={**self.credentials, "password": "wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.cookies.get(settings.session_cookie_name), previous)
        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 200)

    def test_deleted_tutor_cannot_use_existing_cookie(self) -> None:
        data = self.register().json()["data"]
        with SessionLocal() as db:
            db.delete(db.get(User, data["user"]["id"]))
            db.commit()
        self.assertEqual(self.client.get("/api/v1/students").status_code, 401)


class BrowserSessionMigrationTest(unittest.TestCase):
    def test_upgrade_and_downgrade_match_session_model(self) -> None:
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "20261001_0004_browser_sessions.py"
        spec = importlib.util.spec_from_file_location("browser_session_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            User.__table__.create(connection)
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                inspector = inspect(connection)
                self.assertEqual(
                    {column["name"] for column in inspector.get_columns("browser_sessions")},
                    set(BrowserSession.__table__.columns.keys()),
                )
                self.assertEqual(len(inspector.get_indexes("browser_sessions")), 2)
                self.assertEqual(inspector.get_foreign_keys("browser_sessions")[0]["options"]["ondelete"], "CASCADE")
                migration.downgrade()
                self.assertNotIn("browser_sessions", inspect(connection).get_table_names())
        engine.dispose()
