"""Attendance models for attendance tracking."""

from datetime import datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Attendance(Base, TimestampMixin):
    """Attendance record for a person."""

    __tablename__ = "attendance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Person reference
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id"), nullable=False)

    # Attendance date
    attendance_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Check-in information
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_in_detection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("detections.id"),
        nullable=True
    )
    check_in_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    check_in_camera_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=True)
    check_in_source: Mapped[str] = mapped_column(
        String(50),
        default="detection",
        nullable=False,
        comment="detection, manual, import, etc."
    )

    # Check-out information
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_out_detection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("detections.id"),
        nullable=True
    )
    check_out_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    check_out_camera_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=True)
    check_out_source: Mapped[str] = mapped_column(
        String(50),
        default="detection",
        nullable=False
    )

    # Duration
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Attendance status
    status: Mapped[str] = mapped_column(
        String(50),
        default="present",
        nullable=False,
        comment="present, absent, late, early_leave, half_day, excused, etc."
    )

    # Session reference
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("attendance_sessions.id"),
        nullable=True
    )

    # Manual entry flag
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_entry_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    manual_entry_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Approval
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    person = relationship("Person", back_populates="attendance_records")
    session = relationship("AttendanceSession", back_populates="attendance_records")

    # Indexes
    __table_args__ = (
        Index("ix_attendance_person_id", "person_id"),
        Index("ix_attendance_date", "attendance_date"),
        Index("ix_attendance_person_date", "person_id", "attendance_date"),
        Index("ix_attendance_status", "status"),
        Index("ix_attendance_is_manual", "is_manual"),
    )


class AttendanceSession(Base, TimestampMixin):
    """Attendance session/shift for grouping attendance records."""

    __tablename__ = "attendance_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Session information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Session timing
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    expected_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Grace period
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    early_departure_allowed_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    attendance_records = relationship("Attendance", back_populates="session")

    # Indexes
    __table_args__ = (
        Index("ix_attendance_session_is_active", "is_active"),
    )


class AttendanceRule(Base, TimestampMixin):
    """Attendance rules and policies."""

    __tablename__ = "attendance_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Rule information
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rule type
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="working_days, shift_time, grace_period, etc."
    )

    # Rule details
    rule_value: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Applicability
    applies_to: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="all, department, person_type, etc."
    )
    applies_to_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_attendance_rule_is_active", "is_active"),
        Index("ix_attendance_rule_priority", "priority"),
    )


class AttendanceException(Base, TimestampMixin):
    """Exceptions to attendance rules (holidays, leaves, etc.)."""

    __tablename__ = "attendance_exceptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Exception information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Exception type
    exception_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="holiday, leave, special_event, etc."
    )

    # Date range
    from_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    to_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Applicability
    applies_to: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="all, department, person_type, person, etc."
    )
    applies_to_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Created by
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_attendance_exception_from_date", "from_date"),
        Index("ix_attendance_exception_to_date", "to_date"),
        Index("ix_attendance_exception_is_active", "is_active"),
    )
