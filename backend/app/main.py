import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.api.v1.router import api_router
from app.database import Base, engine, get_db

logger = logging.getLogger(__name__)


def init_db() -> None:
    if os.getenv("DATABASE_SCHEMA_MANAGED_BY_ALEMBIC", "false").lower() != "true":
        Base.metadata.create_all(bind=engine)


def frontend_dist() -> Path | None:
    configured_path = os.getenv("FRONTEND_DIST")
    if not configured_path:
        return None
    directory = Path(configured_path).resolve()
    return directory if directory.is_dir() else None


def frontend_response(requested_path: str = ""):
    directory = frontend_dist()
    if directory is None:
        if requested_path:
            raise HTTPException(status_code=404, detail="Not found.")
        return {"message": "TutorFlow API"}

    if requested_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found.")

    requested_file = (directory / requested_path).resolve()
    if requested_path and requested_file.is_relative_to(directory) and requested_file.is_file():
        return FileResponse(requested_file)
    return FileResponse(directory / "index.html")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="TutorFlow API",
    description="TutorFlow AI backend API contract.",
    version="0.3.0",
    lifespan=lifespan,
)
app.include_router(api_router)
db_dependency = Depends(get_db)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": "Request failed.", "detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"success": False, "message": "Validation error.", "detail": exc.errors()}),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Request failed.",
            "detail": "Internal server error.",
        },
    )


@app.get("/")
def root():
    return frontend_response()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def database_health(db: Session = db_dependency):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/{requested_path:path}", include_in_schema=False)
def frontend(requested_path: str):
    return frontend_response(requested_path)
