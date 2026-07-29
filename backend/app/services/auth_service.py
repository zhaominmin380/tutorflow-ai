from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


@dataclass
class LoginResult:
    access_token: str
    token_type: str
    user: User


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def register_user(self, db: Session, email: str, password: str, name: str) -> User:
        existing_user = self.user_repository.get_by_email(db, email)
        if existing_user:
            raise DuplicateEmailError("Email is already registered.")

        password_hash = hash_password(password)
        return self.user_repository.create(db, email=email, password_hash=password_hash, name=name)

    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        return user

    def create_login_result(self, user: User) -> LoginResult:
        access_token = create_access_token(user_id=user.id, email=user.email)
        return LoginResult(access_token=access_token, token_type="bearer", user=user)

    def login_user(self, db: Session, email: str, password: str) -> LoginResult:
        user = self.authenticate_user(db, email, password)
        return self.create_login_result(user)
