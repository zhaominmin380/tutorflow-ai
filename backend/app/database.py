import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return f"postgresql+psycopg://{database_url.removeprefix('postgres://')}"
    if database_url.startswith("postgresql://"):
        return f"postgresql+psycopg://{database_url.removeprefix('postgresql://')}"
    return database_url


DATABASE_URL = normalize_database_url(
    os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://tutorflow:password@localhost:5433/tutorflow",
    )
)

engine_kwargs = {}
if DATABASE_URL == "sqlite:///:memory:":
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
