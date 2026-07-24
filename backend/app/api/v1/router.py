from fastapi import APIRouter

from app.api.v1 import ai, auth, dashboard, lesson_notes, lessons, payments, students


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(lessons.router)
api_router.include_router(lesson_notes.router)
api_router.include_router(payments.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
