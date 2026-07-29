from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def create(self, db: Session, email: str, password_hash: str, name: str) -> User:
        user = User(email=email, password_hash=password_hash, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
