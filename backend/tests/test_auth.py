import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-for-sprint-4"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import decode_access_token, hash_password, verify_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402


class AuthenticationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def register_user(self, email: str = "teacher-auth@example.com") -> dict:
        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "password123", "name": "Teacher"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_password_hashing_and_verification(self) -> None:
        password_hash = hash_password("password123")

        self.assertNotEqual(password_hash, "password123")
        self.assertTrue(verify_password("password123", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_successful_registration_stores_hashed_password(self) -> None:
        self.register_user("stored-hash@example.com")

        db = SessionLocal()
        try:
            user = UserRepository().get_by_email(db, "stored-hash@example.com")
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, "password123")
            self.assertTrue(verify_password("password123", user.password_hash))
        finally:
            db.close()

    def test_duplicate_email_returns_conflict(self) -> None:
        self.register_user("duplicate@example.com")

        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "password123", "name": "Teacher"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["success"])

    def test_successful_login_returns_valid_token(self) -> None:
        self.register_user("login-success@example.com")

        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "login-success@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)
        token = response.json()["data"]["access_token"]
        payload = decode_access_token(token)
        self.assertEqual(payload["email"], "login-success@example.com")
        self.assertIn("exp", payload)

    def test_wrong_password_returns_unauthorized(self) -> None:
        self.register_user("wrong-password@example.com")

        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "wrong-password@example.com", "password": "bad-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_unknown_email_returns_unauthorized(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_protected_api_requires_valid_token(self) -> None:
        missing = self.client.get("/api/v1/students")
        self.assertEqual(missing.status_code, 401)

        invalid = self.client.get("/api/v1/students", headers={"Authorization": "Bearer invalid-token"})
        self.assertEqual(invalid.status_code, 401)

        token = self.register_user("protected@example.com")["data"]["access_token"]
        valid = self.client.get("/api/v1/students", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(valid.status_code, 200)

    def test_expired_token_returns_unauthorized(self) -> None:
        expired_token = jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.require_secret_key(),
            algorithm=settings.algorithm,
        )

        response = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_swagger_defines_oauth2_security_scheme(self) -> None:
        schema = self.client.get("/openapi.json").json()

        self.assertIn("OAuth2PasswordBearer", schema["components"]["securitySchemes"])
        self.assertEqual(
            schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"],
            "/api/v1/auth/token",
        )
        self.assertIn("security", schema["paths"]["/api/v1/auth/me"]["get"])

    def test_swagger_token_endpoint_accepts_oauth2_form_login(self) -> None:
        self.register_user("swagger-token@example.com")

        response = self.client.post(
            "/api/v1/auth/token",
            data={"username": "swagger-token@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())


if __name__ == "__main__":
    unittest.main()
