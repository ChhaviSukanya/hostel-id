from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # = Enrollment No.
    name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="student", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    submission: Mapped[Optional["Submission"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_pk: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    father_name: Mapped[str] = mapped_column(String(150))  # "D/O"
    program: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    hostel: Mapped[str] = mapped_column(String(100))
    dob: Mapped[date] = mapped_column(Date)
    address: Mapped[str] = mapped_column(String(400))
    student_phone: Mapped[str] = mapped_column(String(15))
    parent_phone: Mapped[str] = mapped_column(String(15))
    photo_file: Mapped[str] = mapped_column(String(200))
    signature_file: Mapped[str] = mapped_column(String(200))
    photo_drive_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    signature_drive_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user: Mapped[User] = relationship(back_populates="submission")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(10), default="running")  # running | done | failed
    stage: Mapped[str] = mapped_column(String(200), default="Starting")
    total: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    warnings: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    slides_url: Mapped[str] = mapped_column(String(300), default="")
    pdf_file: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
