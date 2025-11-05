"""Camera-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, validator


# ============================================================================
# Camera Group Schemas
# ============================================================================


class CameraGroupBase(BaseModel):
    """Base camera group schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, max_length=1000, description="Group description")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    order: int = Field(0, ge=0, description="Display order")


class CameraGroupCreate(CameraGroupBase):
    """Create camera group request."""

    pass


class CameraGroupUpdate(BaseModel):
    """Update camera group request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=255)
    order: Optional[int] = Field(None, ge=0)


class CameraGroupResponse(CameraGroupBase):
    """Camera group response."""

    id: str = Field(..., description="Group ID")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Camera Schemas
# ============================================================================


class CameraBase(BaseModel):
    """Base camera schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Camera name")
    description: Optional[str] = Field(None, description="Camera description")
    rtsp_url: str = Field(..., description="RTSP stream URL")
    username: Optional[str] = Field(None, description="RTSP username")
    password: Optional[str] = Field(None, description="RTSP password")

    # Camera specs
    resolution: str = Field("1920x1080", description="Video resolution (e.g., 1920x1080)")
    fps: int = Field(30, ge=1, le=60, description="Frames per second")
    codec: str = Field("h264", description="Video codec (h264, h265, mjpeg)")

    # Location
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")

    # Grouping
    group_id: Optional[str] = Field(None, description="Camera group ID")

    # Feature flags
    is_active: bool = Field(True, description="Camera is active")
    is_primary: bool = Field(False, description="Primary camera for this location")
    enable_recording: bool = Field(False, description="Enable recording")
    enable_snapshots: bool = Field(True, description="Enable snapshots")
    enable_detection: bool = Field(True, description="Enable face detection")
    detection_sensitivity: float = Field(0.7, ge=0.0, le=1.0, description="Detection sensitivity 0-1")

    @validator("rtsp_url")
    def validate_rtsp_url(cls, v):
        """Validate RTSP URL format."""
        if not v.lower().startswith(("rtsp://", "rtsps://")):
            raise ValueError("URL must start with rtsp:// or rtsps://")
        return v

    @validator("codec")
    def validate_codec(cls, v):
        """Validate video codec."""
        valid_codecs = {"h264", "h265", "mjpeg"}
        if v.lower() not in valid_codecs:
            raise ValueError(f"Codec must be one of: {', '.join(valid_codecs)}")
        return v.lower()


class CameraCreate(CameraBase):
    """Create camera request."""

    pass


class CameraUpdate(BaseModel):
    """Update camera request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    rtsp_url: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    resolution: Optional[str] = Field(None)
    fps: Optional[int] = Field(None, ge=1, le=60)
    codec: Optional[str] = Field(None)
    location: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    group_id: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
    is_primary: Optional[bool] = Field(None)
    enable_recording: Optional[bool] = Field(None)
    enable_snapshots: Optional[bool] = Field(None)
    enable_detection: Optional[bool] = Field(None)
    detection_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator("rtsp_url", pre=True, always=False)
    def validate_rtsp_url(cls, v):
        """Validate RTSP URL format if provided."""
        if v and not v.lower().startswith(("rtsp://", "rtsps://")):
            raise ValueError("URL must start with rtsp:// or rtsps://")
        return v


class CameraStateUpdate(BaseModel):
    """Update camera state (minimal)."""

    status: Optional[str] = Field(None, description="Camera status: idle, connecting, live, error")
    is_active: Optional[bool] = Field(None, description="Camera active status")


class CameraResponse(CameraBase):
    """Camera response schema."""

    id: str = Field(..., description="Camera ID")
    status: str = Field(..., description="Current status")
    last_connected: Optional[datetime] = Field(None, description="Last successful connection")
    last_error: Optional[str] = Field(None, description="Last error message")
    connection_retries: int = Field(..., description="Connection retry count")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


class CameraListResponse(BaseModel):
    """Camera list response with optional filters."""

    cameras: list[CameraResponse] = Field(..., description="List of cameras")
    total: int = Field(..., description="Total cameras")
    active: int = Field(..., description="Active cameras")
    offline: int = Field(..., description="Offline cameras")


# ============================================================================
# Camera Health Schemas
# ============================================================================


class CameraHealthResponse(BaseModel):
    """Camera health status response."""

    id: str = Field(..., description="Health record ID")
    camera_id: str = Field(..., description="Camera ID")
    is_connected: bool = Field(..., description="Connected status")
    latency_ms: Optional[int] = Field(None, description="Latency in milliseconds")
    fps_actual: Optional[float] = Field(None, description="Actual FPS")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    bandwidth_mbps: Optional[float] = Field(None, description="Bandwidth in Mbps")
    status_message: Optional[str] = Field(None, description="Status message")
    last_check: datetime = Field(..., description="Last health check timestamp")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Camera Snapshot Schemas
# ============================================================================


class CameraSnapshotResponse(BaseModel):
    """Camera snapshot response."""

    id: str = Field(..., description="Snapshot ID")
    camera_id: str = Field(..., description="Camera ID")
    filename: str = Field(..., description="Filename")
    file_size: int = Field(..., description="File size in bytes")
    storage_path: str = Field(..., description="MinIO storage path")
    mime_type: str = Field(..., description="MIME type")
    resolution: str = Field(..., description="Image resolution")
    thumbnail_path: Optional[str] = Field(None, description="Thumbnail storage path")
    is_processing: bool = Field(..., description="Processing status")
    is_archived: bool = Field(..., description="Archived status")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Camera Operation Schemas
# ============================================================================


class CameraConnectionTestRequest(BaseModel):
    """Request to test camera connection."""

    timeout_seconds: int = Field(10, ge=5, le=60, description="Connection timeout in seconds")
    check_credentials: bool = Field(True, description="Validate credentials")


class CameraConnectionTestResponse(BaseModel):
    """Camera connection test response."""

    success: bool = Field(..., description="Connection successful")
    camera_id: str = Field(..., description="Camera ID")
    message: str = Field(..., description="Result message")
    latency_ms: Optional[int] = Field(None, description="Latency in milliseconds")
    resolution: Optional[str] = Field(None, description="Detected resolution")
    fps: Optional[int] = Field(None, description="Detected FPS")
    error: Optional[str] = Field(None, description="Error details")


class CameraSnapshotRequest(BaseModel):
    """Request to capture snapshot."""

    timeout_seconds: int = Field(10, ge=5, le=30, description="Capture timeout")
    save_thumbnail: bool = Field(True, description="Generate thumbnail")


class CameraSnapshotResponse(BaseModel):
    """Camera snapshot capture response."""

    success: bool = Field(..., description="Snapshot captured successfully")
    camera_id: str = Field(..., description="Camera ID")
    snapshot_id: Optional[str] = Field(None, description="Snapshot record ID")
    storage_path: Optional[str] = Field(None, description="MinIO storage path")
    url: Optional[str] = Field(None, description="Snapshot URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    error: Optional[str] = Field(None, description="Error details")


class CameraImportRequest(BaseModel):
    """Request to import cameras from CSV/JSON."""

    format: str = Field("csv", description="Import format: csv or json")
    data: str = Field(..., description="Base64 encoded file content")
    group_id: Optional[str] = Field(None, description="Group to assign cameras to")
    skip_duplicates: bool = Field(True, description="Skip duplicate RTSP URLs")


class CameraImportResponse(BaseModel):
    """Camera import response."""

    success: bool = Field(..., description="Import successful")
    imported_count: int = Field(..., description="Number of cameras imported")
    skipped_count: int = Field(..., description="Number of cameras skipped")
    errors: list[dict] = Field(default_factory=list, description="Import errors")


class CameraExportRequest(BaseModel):
    """Request to export cameras."""

    format: str = Field("csv", description="Export format: csv or json")
    include_credentials: bool = Field(False, description="Include RTSP credentials")
    group_id: Optional[str] = Field(None, description="Export only from this group")


class CameraExportResponse(BaseModel):
    """Camera export response."""

    success: bool = Field(..., description="Export successful")
    format: str = Field(..., description="Export format")
    data: str = Field(..., description="Base64 encoded exported data")
    camera_count: int = Field(..., description="Number of cameras exported")
    filename: str = Field(..., description="Suggested filename")


class CameraSummaryResponse(BaseModel):
    """Camera system summary."""

    total_cameras: int = Field(..., description="Total cameras")
    active_cameras: int = Field(..., description="Active cameras")
    offline_cameras: int = Field(..., description="Offline cameras")
    recording_cameras: int = Field(..., description="Recording cameras")
    detection_enabled: int = Field(..., description="Detection enabled cameras")
    total_groups: int = Field(..., description="Total groups")
    last_update: datetime = Field(..., description="Last update timestamp")
    health_check_status: str = Field(..., description="Overall health status: healthy, warning, critical")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency")
    system_uptime_hours: Optional[float] = Field(None, description="System uptime in hours")


__all__ = [
    "CameraGroupBase",
    "CameraGroupCreate",
    "CameraGroupUpdate",
    "CameraGroupResponse",
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraStateUpdate",
    "CameraResponse",
    "CameraListResponse",
    "CameraHealthResponse",
    "CameraSnapshotResponse",
    "CameraConnectionTestRequest",
    "CameraConnectionTestResponse",
    "CameraSnapshotRequest",
    "CameraImportRequest",
    "CameraImportResponse",
    "CameraExportRequest",
    "CameraExportResponse",
    "CameraSummaryResponse",
]
