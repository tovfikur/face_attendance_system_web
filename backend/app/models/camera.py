"""Camera-related database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CameraGroup(Base, TimestampMixin):
    """Camera group model for organizing cameras."""

    __tablename__ = "camera_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    cameras: Mapped[list["Camera"]] = relationship("Camera", back_populates="group")

    __table_args__ = (Index("idx_camera_groups_name", "name"),)

    def __repr__(self) -> str:
        return f"<CameraGroup id={self.id} name={self.name}>"


class Camera(Base, TimestampMixin):
    """Camera model for CCTV system."""

    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Connection details
    rtsp_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Camera specs
    resolution: Mapped[str] = mapped_column(String(50), default="1920x1080")  # e.g. "1920x1080"
    fps: Mapped[int] = mapped_column(Integer, default=30)
    codec: Mapped[str] = mapped_column(String(50), default="h264")  # h264, h265, mjpeg

    # Location info
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)

    # Grouping
    group_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("camera_groups.id"), nullable=True, index=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="idle")  # idle, connecting, live, error
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Feature flags
    enable_recording: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_snapshots: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_detection: Mapped[bool] = mapped_column(Boolean, default=True)
    detection_sensitivity: Mapped[float] = mapped_column(Float, default=0.7)  # 0.0 - 1.0

    # Connection tracking
    last_connected: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    connection_retries: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    group: Mapped[Optional[CameraGroup]] = relationship("CameraGroup", back_populates="cameras")
    health_records: Mapped[list["CameraHealth"]] = relationship("CameraHealth", back_populates="camera", cascade="all, delete-orphan")
    snapshots: Mapped[list["CameraSnapshot"]] = relationship("CameraSnapshot", back_populates="camera", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_cameras_name", "name"),
        Index("idx_cameras_status", "status"),
        Index("idx_cameras_group_id", "group_id"),
        Index("idx_cameras_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Camera id={self.id} name={self.name} status={self.status}>"


class CameraHealth(Base, TimestampMixin):
    """Camera health monitoring record."""

    __tablename__ = "camera_health"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)

    # Health metrics
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # milliseconds
    fps_actual: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # percentage
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # percentage
    bandwidth_mbps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    status_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_check: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    camera: Mapped[Camera] = relationship("Camera", back_populates="health_records")

    __table_args__ = (
        Index("idx_camera_health_camera_id", "camera_id"),
        Index("idx_camera_health_last_check", "last_check"),
    )

    def __repr__(self) -> str:
        return f"<CameraHealth camera_id={self.camera_id} is_connected={self.is_connected}>"


class CameraSnapshot(Base, TimestampMixin):
    """Camera snapshot record for storage tracking."""

    __tablename__ = "camera_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)

    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer)  # in bytes
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)  # MinIO path
    mime_type: Mapped[str] = mapped_column(String(100), default="image/jpeg")

    # Metadata
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)  # "1920x1080"
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Lifecycle
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    camera: Mapped[Camera] = relationship("Camera", back_populates="snapshots")

    __table_args__ = (
        Index("idx_camera_snapshots_camera_id", "camera_id"),
        Index("idx_camera_snapshots_created_at", "created_at"),
        Index("idx_camera_snapshots_expiry", "expiry_date"),
    )

    def __repr__(self) -> str:
        return f"<CameraSnapshot id={self.id} camera_id={self.camera_id}>"
