from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LessonStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    students: Mapped[list[Student]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_logs: Mapped[list[AILog]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    school: Mapped[str | None] = mapped_column(String(100))
    grade: Mapped[str | None] = mapped_column(String(50))
    subject: Mapped[str | None] = mapped_column(String(100))
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="students")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(
            LessonStatus,
            name="lesson_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=LessonStatus.SCHEDULED,
        server_default=LessonStatus.SCHEDULED.value,
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(String(255))
    remark: Mapped[str | None] = mapped_column(Text)

    student: Mapped[Student] = relationship(back_populates="lessons")
    lesson_note: Mapped[LessonNote | None] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        uselist=False,
    )
    payment: Mapped[Payment | None] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        uselist=False,
    )


class LessonNote(TimestampMixin, Base):
    __tablename__ = "lesson_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    raw_note: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    teacher_note: Mapped[str | None] = mapped_column(Text)
    parent_feedback: Mapped[str | None] = mapped_column(Text)

    lesson: Mapped[Lesson] = relationship(back_populates="lesson_note")


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lesson: Mapped[Lesson] = relationship(back_populates="payment")


class AILog(TimestampMixin, Base):
    __tablename__ = "ai_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    log_type: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="ai_logs")
