"""Person-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Person Schemas
# ============================================================================


class PersonBase(BaseModel):
    """Base person schema."""

    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    person_type: str = Field(..., description="Person type (employee, visitor, contractor)")
    id_number: Optional[str] = Field(None, description="ID number")
    id_type: Optional[str] = Field(None, description="ID type (passport, national_id, etc.)")

    department: Optional[str] = Field(None, description="Department")
    organization: Optional[str] = Field(None, description="Organization")

    status: str = Field("active", description="Status (active, inactive, deleted)")


class PersonCreate(PersonBase):
    """Create person request."""

    pass


class PersonUpdate(BaseModel):
    """Update person request."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=20)

    person_type: Optional[str] = Field(None)
    id_number: Optional[str] = Field(None)
    id_type: Optional[str] = Field(None)

    department: Optional[str] = Field(None)
    organization: Optional[str] = Field(None)

    status: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


class PersonResponse(PersonBase):
    """Person response schema."""

    id: str = Field(..., description="Person ID")
    face_encoding_count: int = Field(..., description="Number of face encodings")
    enrolled_at: Optional[datetime] = Field(None, description="Enrollment date")
    last_face_enrolled: Optional[datetime] = Field(None, description="Last face enrollment date")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Face Encoding Schemas
# ============================================================================


class FaceEncodingBase(BaseModel):
    """Base face encoding schema."""

    encoding_model: str = Field("dlib_128d", description="Encoding model")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Encoding confidence")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Image quality score")


class FaceEncodingResponse(FaceEncodingBase):
    """Face encoding response schema."""

    id: str = Field(..., description="Encoding ID")
    person_id: str = Field(..., description="Person ID")
    is_active: bool = Field(..., description="Is active")
    source_image_id: Optional[str] = Field(None, description="Source image ID")
    createdAt: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Person Image Schemas
# ============================================================================


class PersonImageBase(BaseModel):
    """Base person image schema."""

    is_primary: bool = Field(False, description="Is primary image")


class PersonImageResponse(PersonImageBase):
    """Person image response schema."""

    id: str = Field(..., description="Image ID")
    person_id: str = Field(..., description="Person ID")
    filename: str = Field(..., description="Filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")

    image_width: Optional[int] = Field(None, description="Image width")
    image_height: Optional[int] = Field(None, description="Image height")
    quality_score: Optional[float] = Field(None, description="Quality score")

    face_detected: bool = Field(..., description="Face detected in image")
    face_confidence: Optional[float] = Field(None, description="Face detection confidence")

    createdAt: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Person Enrollment Schemas
# ============================================================================


class PersonEnrollmentRequest(BaseModel):
    """Request to enroll a face for a person."""

    frame_data: str = Field(..., description="Base64 encoded frame/image")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Image quality")
    is_primary: bool = Field(False, description="Set as primary image")


class PersonEnrollmentResponse(BaseModel):
    """Response for face enrollment."""

    success: bool = Field(..., description="Enrollment successful")
    person_id: str = Field(..., description="Person ID")
    encoding_id: str = Field(..., description="Encoding ID")
    face_detected: bool = Field(..., description="Face detected")
    face_confidence: float = Field(..., description="Face detection confidence")
    quality_score: float = Field(..., description="Image quality score")
    total_encodings: int = Field(..., description="Total encodings for person")
    message: str = Field(..., description="Result message")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Person Search Schemas
# ============================================================================


class PersonSearchRequest(BaseModel):
    """Request to search for person by attributes."""

    query: Optional[str] = Field(None, description="Search query (name, email, etc.)")
    person_type: Optional[str] = Field(None, description="Filter by person type")
    department: Optional[str] = Field(None, description="Filter by department")
    status: Optional[str] = Field(None, description="Filter by status")


class PersonSearchByFaceRequest(BaseModel):
    """Request to find person by face."""

    frame_data: str = Field(..., description="Base64 encoded face image")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Match confidence threshold")


class PersonFaceMatchResult(BaseModel):
    """Result of face matching."""

    person_id: str = Field(..., description="Person ID")
    person_name: str = Field(..., description="Person name")
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")
    encoding_id: str = Field(..., description="Matching encoding ID")


class PersonSearchByFaceResponse(BaseModel):
    """Response for face search."""

    matches: list[PersonFaceMatchResult] = Field(..., description="Matched persons")
    best_match: Optional[PersonFaceMatchResult] = Field(None, description="Best match")
    total_matches: int = Field(..., description="Total matches")


# ============================================================================
# Attendance Schemas
# ============================================================================


class AttendanceBase(BaseModel):
    """Base attendance schema."""

    attendance_date: datetime = Field(..., description="Attendance date")
    status: str = Field("present", description="Status (present, absent, late, etc.)")


class AttendanceCreate(AttendanceBase):
    """Create attendance request."""

    person_id: str = Field(..., description="Person ID")
    check_in_time: Optional[datetime] = Field(None, description="Check-in time")
    check_out_time: Optional[datetime] = Field(None, description="Check-out time")


class AttendanceUpdate(BaseModel):
    """Update attendance request."""

    status: Optional[str] = Field(None, description="Status")
    check_in_time: Optional[datetime] = Field(None, description="Check-in time")
    check_out_time: Optional[datetime] = Field(None, description="Check-out time")
    notes: Optional[str] = Field(None, description="Notes")


class AttendanceResponse(AttendanceBase):
    """Attendance response schema."""

    id: str = Field(..., description="Attendance ID")
    person_id: str = Field(..., description="Person ID")

    check_in_time: Optional[datetime] = Field(None, description="Check-in time")
    check_in_confidence: float = Field(..., description="Check-in confidence")
    check_in_source: str = Field(..., description="Check-in source")

    check_out_time: Optional[datetime] = Field(None, description="Check-out time")
    check_out_confidence: float = Field(..., description="Check-out confidence")
    check_out_source: str = Field(..., description="Check-out source")

    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    is_manual: bool = Field(..., description="Is manual entry")

    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Attendance Statistics Schemas
# ============================================================================


class AttendanceStatistics(BaseModel):
    """Attendance statistics."""

    total_working_days: int = Field(..., description="Total working days")
    days_present: int = Field(..., description="Days present")
    days_absent: int = Field(..., description="Days absent")
    days_late: int = Field(..., description="Days late")
    days_early_leave: int = Field(..., description="Days with early leave")
    presence_percentage: float = Field(..., description="Presence percentage")
    average_check_in_delay_minutes: Optional[float] = Field(None, description="Average check-in delay")


class AttendanceReport(BaseModel):
    """Attendance report for a person."""

    person_id: str = Field(..., description="Person ID")
    person_name: str = Field(..., description="Person name")
    from_date: datetime = Field(..., description="Report from date")
    to_date: datetime = Field(..., description="Report to date")

    attendance_records: list[AttendanceResponse] = Field(..., description="Attendance records")
    statistics: AttendanceStatistics = Field(..., description="Statistics")


# ============================================================================
# Check-in/Check-out Schemas
# ============================================================================


class CheckInRequest(BaseModel):
    """Request to mark check-in."""

    person_id: Optional[str] = Field(None, description="Person ID (if known)")
    frame_data: Optional[str] = Field(None, description="Face frame (if auto-detection)")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold")


class CheckInResponse(BaseModel):
    """Response for check-in."""

    success: bool = Field(..., description="Check-in successful")
    person_id: str = Field(..., description="Person ID")
    person_name: str = Field(..., description="Person name")
    check_in_time: datetime = Field(..., description="Check-in time")
    confidence: float = Field(..., description="Detection confidence")
    message: str = Field(..., description="Result message")
    error: Optional[str] = Field(None, description="Error message if failed")


class CheckOutRequest(BaseModel):
    """Request to mark check-out."""

    person_id: str = Field(..., description="Person ID")
    frame_data: Optional[str] = Field(None, description="Face frame (if verification)")


class CheckOutResponse(BaseModel):
    """Response for check-out."""

    success: bool = Field(..., description="Check-out successful")
    person_id: str = Field(..., description="Person ID")
    person_name: str = Field(..., description="Person name")
    check_out_time: datetime = Field(..., description="Check-out time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    message: str = Field(..., description="Result message")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Current Status Schema
# ============================================================================


class PersonCurrentStatus(BaseModel):
    """Current check-in status for a person."""

    person_id: str = Field(..., description="Person ID")
    person_name: str = Field(..., description="Person name")
    checked_in: bool = Field(..., description="Currently checked in")
    check_in_time: Optional[datetime] = Field(None, description="Check-in time")
    current_duration_minutes: Optional[int] = Field(None, description="Current duration")
    last_detection_time: Optional[datetime] = Field(None, description="Last detection time")
    last_detection_location: Optional[str] = Field(None, description="Last detection location")


__all__ = [
    "PersonBase",
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    "FaceEncodingResponse",
    "PersonImageResponse",
    "PersonEnrollmentRequest",
    "PersonEnrollmentResponse",
    "PersonSearchRequest",
    "PersonSearchByFaceRequest",
    "PersonFaceMatchResult",
    "PersonSearchByFaceResponse",
    "AttendanceBase",
    "AttendanceCreate",
    "AttendanceUpdate",
    "AttendanceResponse",
    "AttendanceStatistics",
    "AttendanceReport",
    "CheckInRequest",
    "CheckInResponse",
    "CheckOutRequest",
    "CheckOutResponse",
    "PersonCurrentStatus",
]
