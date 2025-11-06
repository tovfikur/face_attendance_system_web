"""Person models for person management."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Person(Base, TimestampMixin):
    """Person/employee/visitor profile."""

    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Person type
    person_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="employee, visitor, contractor, other"
    )

    # Identity information
    id_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    id_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="passport, national_id, driver_license, etc."
    )

    # Department/organization
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        comment="active, inactive, deleted, suspended"
    )

    # Enrollment information
    enrolled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enrolled_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Face encoding availability
    face_encoding_count: Mapped[int] = mapped_column(default=0)
    last_face_enrolled: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="JSON metadata")

    # Relations
    face_encodings = relationship(
        "PersonFaceEncoding",
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    images = relationship(
        "PersonImage",
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    attendance_records = relationship(
        "Attendance",
        back_populates="person",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_person_email", "email"),
        Index("ix_person_id_number", "id_number"),
        Index("ix_person_status", "status"),
        Index("ix_person_person_type", "person_type"),
        Index("ix_person_department", "department"),
        Index("ix_person_created_at", "created_at"),
    )


class PersonFaceEncoding(Base, TimestampMixin):
    """Face encoding vector for a person."""

    __tablename__ = "person_face_encodings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Person reference
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id"), nullable=False)

    # Face encoding (512-dimensional vector from face_recognition library)
    # Stored as binary data for efficiency
    encoding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Encoding metadata
    encoding_model: Mapped[str] = mapped_column(
        String(100),
        default="dlib_128d",
        nullable=False,
        comment="Model used to generate encoding"
    )

    # Quality metrics
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    quality_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Image quality score 0.0-1.0"
    )

    # Image source
    source_image_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("person_images.id"),
        nullable=True
    )

    # Detection reference (if created from detection)
    source_detection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("detections.id"),
        nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    person = relationship("Person", back_populates="face_encodings")
    image = relationship("PersonImage", back_populates="encodings")

    # Indexes
    __table_args__ = (
        Index("ix_person_face_encoding_person_id", "person_id"),
        Index("ix_person_face_encoding_is_active", "is_active"),
        Index("ix_person_face_encoding_confidence", "confidence"),
    )


class PersonImage(Base, TimestampMixin):
    """Face image for a person."""

    __tablename__ = "person_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Person reference
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("persons.id"), nullable=False)

    # Image file information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="MinIO path")
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Image metadata
    image_width: Mapped[Optional[int]] = mapped_column(nullable=True)
    image_height: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Image quality
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_blurry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Face detection
    face_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    face_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Status
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Source
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    source_detection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("detections.id"),
        nullable=True,
        comment="If created from detection"
    )

    # Relations
    person = relationship("Person", back_populates="images")
    encodings = relationship(
        "PersonFaceEncoding",
        back_populates="image",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_person_image_person_id", "person_id"),
        Index("ix_person_image_is_active", "is_active"),
        Index("ix_person_image_face_detected", "face_detected"),
        Index("ix_person_image_is_primary", "is_primary"),
    )


class PersonMetadata(Base, TimestampMixin):
    """Additional metadata for persons."""

    __tablename__ = "person_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Person reference
    person_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("persons.id"),
        nullable=False,
        unique=True
    )

    # Enrollment details
    enrollment_method: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="self_enrollment, admin_added, import, etc."
    )

    # Preferences
    preferred_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Additional fields
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Custom fields (JSON)
    custom_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="JSON")

    # Indexes
    __table_args__ = (
        Index("ix_person_metadata_person_id", "person_id"),
    )
