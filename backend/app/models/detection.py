"""Detection-related database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DetectionProviderConfig(Base, TimestampMixin):
    """Detection provider configuration model."""

    __tablename__ = "detection_provider_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Provider info
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(50))  # e.g., "http_api", "grpc", "mqtt"

    # Connection details
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Encrypted
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Encrypted

    # Configuration
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    max_faces_per_frame: Mapped[int] = mapped_column(Integer, default=10)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7)  # 0.0 - 1.0
    enable_person_detection: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_face_detection: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_face_encoding: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_tested: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_status: Mapped[str] = mapped_column(String(50), default="untested")  # untested, success, failed

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("idx_detection_provider_name", "provider_name"),
        Index("idx_detection_provider_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<DetectionProviderConfig id={self.id} provider={self.provider_name}>"


class Detection(Base, TimestampMixin):
    """Person/Face detection record model."""

    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)

    # Detection info
    detection_type: Mapped[str] = mapped_column(String(50))  # "person", "face", "vehicle", etc.
    confidence: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0

    # Face encoding (optional, for face recognition)
    face_encoding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Serialized numpy array/embedding

    # Bounding box
    bbox_x: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0 (normalized)
    bbox_y: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0 (normalized)
    bbox_width: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0 (normalized)
    bbox_height: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0 (normalized)

    # Optional: linked to known person
    person_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # Link to face/person record
    person_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed

    # Frame info
    frame_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frame_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for additional fields

    __table_args__ = (
        Index("idx_detections_camera_id", "camera_id"),
        Index("idx_detections_detection_type", "detection_type"),
        Index("idx_detections_is_processed", "is_processed"),
        Index("idx_detections_created_at", "created_at"),
        Index("idx_detections_person_id", "person_id"),
    )

    def __repr__(self) -> str:
        return f"<Detection id={self.id} type={self.detection_type} camera={self.camera_id}>"


class DetectionEventLog(Base, TimestampMixin):
    """Detection event log for audit trail and analytics."""

    __tablename__ = "detection_event_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_id: Mapped[str] = mapped_column(String(36), ForeignKey("detections.id"), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)

    # Event info
    event_type: Mapped[str] = mapped_column(String(100))  # e.g., "face_detected", "person_entered", "person_exited"
    severity: Mapped[str] = mapped_column(String(50), default="info")  # info, warning, alert, critical
    message: Mapped[str] = mapped_column(Text)

    # Associated data
    person_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    person_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Actions taken (for alerts)
    action_taken: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "alert_sent", "recording_started"
    action_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    source_system: Mapped[str] = mapped_column(String(50), default="detection_engine")
    extra_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    __table_args__ = (
        Index("idx_detection_events_camera_id", "camera_id"),
        Index("idx_detection_events_detection_id", "detection_id"),
        Index("idx_detection_events_event_type", "event_type"),
        Index("idx_detection_events_severity", "severity"),
        Index("idx_detection_events_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DetectionEventLog id={self.id} event={self.event_type}>"


class DetectionProcessingQueue(Base, TimestampMixin):
    """Queue for detection frames waiting to be processed."""

    __tablename__ = "detection_processing_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)

    # Frame data
    frame_number: Mapped[int] = mapped_column(Integer, index=True)
    frame_path: Mapped[str] = mapped_column(String(512))  # MinIO path to frame
    frame_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Processing status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = more important
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Results
    detections_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    provider_config_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("idx_processing_queue_status", "status"),
        Index("idx_processing_queue_camera_id", "camera_id"),
        Index("idx_processing_queue_priority", "priority"),
        Index("idx_processing_queue_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DetectionProcessingQueue id={self.id} camera={self.camera_id} status={self.status}>"
