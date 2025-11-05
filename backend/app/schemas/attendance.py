"""Attendance-related Pydantic schemas."""

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Attendance Session Schemas
# ============================================================================


class AttendanceSessionBase(BaseModel):
    """Base attendance session schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Session name")
    description: Optional[str] = Field(None, description="Session description")

    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    expected_duration_minutes: int = Field(..., ge=1, description="Expected duration in minutes")

    grace_period_minutes: int = Field(5, ge=0, description="Grace period in minutes")
    early_departure_allowed_minutes: int = Field(15, ge=0, description="Early departure allowance")


class AttendanceSessionCreate(AttendanceSessionBase):
    """Create attendance session request."""

    pass


class AttendanceSessionUpdate(BaseModel):
    """Update attendance session request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)

    start_time: Optional[time] = Field(None)
    end_time: Optional[time] = Field(None)
    expected_duration_minutes: Optional[int] = Field(None, ge=1)

    grace_period_minutes: Optional[int] = Field(None, ge=0)
    early_departure_allowed_minutes: Optional[int] = Field(None, ge=0)


class AttendanceSessionResponse(AttendanceSessionBase):
    """Attendance session response schema."""

    id: str = Field(..., description="Session ID")
    is_active: bool = Field(..., description="Is active")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Attendance Rule Schemas
# ============================================================================


class AttendanceRuleBase(BaseModel):
    """Base attendance rule schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")

    rule_type: str = Field(..., description="Rule type")
    rule_value: str = Field(..., description="Rule value")
    rule_threshold: Optional[float] = Field(None, description="Rule threshold")

    applies_to: str = Field(..., description="Applies to (all, department, etc.)")
    applies_to_value: Optional[str] = Field(None, description="Applies to value")

    priority: int = Field(100, description="Rule priority")


class AttendanceRuleCreate(AttendanceRuleBase):
    """Create attendance rule request."""

    pass


class AttendanceRuleUpdate(BaseModel):
    """Update attendance rule request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)

    rule_type: Optional[str] = Field(None)
    rule_value: Optional[str] = Field(None)
    rule_threshold: Optional[float] = Field(None)

    applies_to: Optional[str] = Field(None)
    applies_to_value: Optional[str] = Field(None)

    priority: Optional[int] = Field(None)


class AttendanceRuleResponse(AttendanceRuleBase):
    """Attendance rule response schema."""

    id: str = Field(..., description="Rule ID")
    is_active: bool = Field(..., description="Is active")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Attendance Exception Schemas
# ============================================================================


class AttendanceExceptionBase(BaseModel):
    """Base attendance exception schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Exception name")
    description: Optional[str] = Field(None, description="Exception description")

    exception_type: str = Field(..., description="Exception type (holiday, leave, etc.)")

    from_date: datetime = Field(..., description="From date")
    to_date: datetime = Field(..., description="To date")

    applies_to: str = Field(..., description="Applies to (all, department, etc.)")
    applies_to_value: Optional[str] = Field(None, description="Applies to value")


class AttendanceExceptionCreate(AttendanceExceptionBase):
    """Create attendance exception request."""

    pass


class AttendanceExceptionUpdate(BaseModel):
    """Update attendance exception request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)

    exception_type: Optional[str] = Field(None)

    from_date: Optional[datetime] = Field(None)
    to_date: Optional[datetime] = Field(None)

    applies_to: Optional[str] = Field(None)
    applies_to_value: Optional[str] = Field(None)


class AttendanceExceptionResponse(AttendanceExceptionBase):
    """Attendance exception response schema."""

    id: str = Field(..., description="Exception ID")
    is_active: bool = Field(..., description="Is active")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Attendance Query Schemas
# ============================================================================


class AttendanceQueryFilters(BaseModel):
    """Filters for attendance queries."""

    person_id: Optional[str] = Field(None, description="Filter by person")
    from_date: Optional[datetime] = Field(None, description="From date")
    to_date: Optional[datetime] = Field(None, description="To date")
    status: Optional[str] = Field(None, description="Filter by status")
    is_manual: Optional[bool] = Field(None, description="Filter by manual entries")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class DailyAttendanceSummary(BaseModel):
    """Daily attendance summary."""

    date: datetime = Field(..., description="Date")
    total_persons: int = Field(..., description="Total persons")
    present: int = Field(..., description="Present count")
    absent: int = Field(..., description="Absent count")
    late: int = Field(..., description="Late count")
    early_leave: int = Field(..., description="Early leave count")
    presence_percentage: float = Field(..., description="Presence percentage")


class MonthlyAttendanceSummary(BaseModel):
    """Monthly attendance summary."""

    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
    total_working_days: int = Field(..., description="Total working days")
    total_persons: int = Field(..., description="Total persons")

    total_present_records: int = Field(..., description="Total present records")
    total_absent_records: int = Field(..., description="Total absent records")
    total_late_records: int = Field(..., description="Total late records")

    average_presence_percentage: float = Field(..., description="Average presence percentage")
    daily_summaries: list[DailyAttendanceSummary] = Field(..., description="Daily summaries")


__all__ = [
    "AttendanceSessionBase",
    "AttendanceSessionCreate",
    "AttendanceSessionUpdate",
    "AttendanceSessionResponse",
    "AttendanceRuleBase",
    "AttendanceRuleCreate",
    "AttendanceRuleUpdate",
    "AttendanceRuleResponse",
    "AttendanceExceptionBase",
    "AttendanceExceptionCreate",
    "AttendanceExceptionUpdate",
    "AttendanceExceptionResponse",
    "AttendanceQueryFilters",
    "DailyAttendanceSummary",
    "MonthlyAttendanceSummary",
]
