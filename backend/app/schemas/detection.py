"""Detection-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Detection Provider Config Schemas
# ============================================================================


class DetectionProviderConfigBase(BaseModel):
    """Base detection provider config schema."""

    provider_name: str = Field(..., min_length=1, max_length=100, description="Provider name")
    provider_type: str = Field(..., description="Provider type (http_api, grpc, mqtt)")
    endpoint_url: str = Field(..., description="Provider endpoint URL")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout")
    max_faces_per_frame: int = Field(10, ge=1, le=100, description="Max faces per frame")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Detection confidence threshold")
    enable_person_detection: bool = Field(True, description="Enable person detection")
    enable_face_detection: bool = Field(True, description="Enable face detection")
    enable_face_encoding: bool = Field(True, description="Enable face encoding")
    is_active: bool = Field(True, description="Provider is active")


class DetectionProviderConfigCreate(DetectionProviderConfigBase):
    """Create detection provider config request."""

    pass


class DetectionProviderConfigUpdate(BaseModel):
    """Update detection provider config request."""

    provider_name: Optional[str] = Field(None, min_length=1, max_length=100)
    endpoint_url: Optional[str] = Field(None)
    api_key: Optional[str] = Field(None)
    api_secret: Optional[str] = Field(None)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=120)
    max_faces_per_frame: Optional[int] = Field(None, ge=1, le=100)
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    enable_person_detection: Optional[bool] = Field(None)
    enable_face_detection: Optional[bool] = Field(None)
    enable_face_encoding: Optional[bool] = Field(None)
    is_active: Optional[bool] = Field(None)


class DetectionProviderConfigResponse(DetectionProviderConfigBase):
    """Detection provider config response."""

    id: str = Field(..., description="Config ID")
    last_tested: Optional[datetime] = Field(None, description="Last test timestamp")
    test_status: str = Field(..., description="Test status: untested, success, failed")
    last_error: Optional[str] = Field(None, description="Last error message")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Detection Schemas
# ============================================================================


class BoundingBox(BaseModel):
    """Bounding box for detection."""

    x: float = Field(..., ge=0.0, le=1.0, description="X coordinate (normalized)")
    y: float = Field(..., ge=0.0, le=1.0, description="Y coordinate (normalized)")
    width: float = Field(..., ge=0.0, le=1.0, description="Width (normalized)")
    height: float = Field(..., ge=0.0, le=1.0, description="Height (normalized)")


class DetectionBase(BaseModel):
    """Base detection schema."""

    detection_type: str = Field(..., description="Detection type: person, face, vehicle")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bbox: BoundingBox = Field(..., description="Bounding box")
    person_name: Optional[str] = Field(None, description="Recognized person name")
    person_id: Optional[str] = Field(None, description="Linked person ID")
    face_encoding: Optional[str] = Field(None, description="Face encoding vector")


class DetectionResponse(DetectionBase):
    """Detection response schema."""

    id: str = Field(..., description="Detection ID")
    camera_id: str = Field(..., description="Camera ID")
    is_processed: bool = Field(..., description="Processed status")
    processing_status: str = Field(..., description="Processing status")
    frame_number: Optional[int] = Field(None, description="Frame number")
    frame_timestamp: Optional[datetime] = Field(None, description="Frame timestamp")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


class LiveDetectionsResponse(BaseModel):
    """Live detections response."""

    camera_id: str = Field(..., description="Camera ID")
    detections: list[DetectionResponse] = Field(..., description="List of detections")
    total_detections: int = Field(..., description="Total detections")
    last_updated: datetime = Field(..., description="Last update timestamp")
    cache_hit: bool = Field(..., description="Whether result came from cache")


# ============================================================================
# Detection Event Schemas
# ============================================================================


class DetectionEventLogResponse(BaseModel):
    """Detection event log response."""

    id: str = Field(..., description="Event ID")
    detection_id: str = Field(..., description="Detection ID")
    camera_id: str = Field(..., description="Camera ID")
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity: info, warning, alert, critical")
    message: str = Field(..., description="Event message")
    person_id: Optional[str] = Field(None, description="Person ID")
    person_name: Optional[str] = Field(None, description="Person name")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    action_taken: Optional[str] = Field(None, description="Action taken")
    action_timestamp: Optional[datetime] = Field(None, description="Action timestamp")
    source_system: str = Field(..., description="Source system")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


# ============================================================================
# Detection Operation Schemas
# ============================================================================


class SendFrameRequest(BaseModel):
    """Send frame for detection request."""

    camera_id: str = Field(..., description="Camera ID")
    frame_data: str = Field(..., description="Base64 encoded frame")
    frame_number: Optional[int] = Field(None, description="Frame number")
    timestamp: Optional[datetime] = Field(None, description="Frame timestamp")


class SendFrameResponse(BaseModel):
    """Send frame response."""

    success: bool = Field(..., description="Request successful")
    camera_id: str = Field(..., description="Camera ID")
    detection_count: int = Field(..., description="Number of detections")
    detections: list[DetectionResponse] = Field(default_factory=list, description="Detected objects")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")


class TestDetectionProviderRequest(BaseModel):
    """Test detection provider request."""

    provider_config_id: Optional[str] = Field(None, description="Config ID (if null, use active config)")
    timeout_seconds: int = Field(10, ge=5, le=120, description="Test timeout")


class TestDetectionProviderResponse(BaseModel):
    """Test detection provider response."""

    success: bool = Field(..., description="Test successful")
    provider_name: str = Field(..., description="Provider name")
    message: str = Field(..., description="Result message")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error details")


# ============================================================================
# Live Detections Query Schemas
# ============================================================================


class LiveDetectionsQuery(BaseModel):
    """Query parameters for live detections."""

    camera_id: Optional[str] = Field(None, description="Filter by camera")
    detection_type: Optional[str] = Field(None, description="Filter by type (person, face)")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class DetectionEventsQuery(BaseModel):
    """Query parameters for detection events."""

    camera_id: Optional[str] = Field(None, description="Filter by camera")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    severity: Optional[str] = Field(None, description="Filter by severity")
    person_id: Optional[str] = Field(None, description="Filter by person")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class DetectionStatisticsResponse(BaseModel):
    """Detection statistics response."""

    total_detections: int = Field(..., description="Total detections")
    detections_today: int = Field(..., description="Detections today")
    detections_this_hour: int = Field(..., description="Detections this hour")
    average_confidence: float = Field(..., description="Average confidence score")
    most_detected_person: Optional[str] = Field(None, description="Most frequently detected person")
    detection_types: dict = Field(..., description="Detection count by type")
    cameras_active: int = Field(..., description="Number of active cameras with detections")
    last_detection_timestamp: Optional[datetime] = Field(None, description="Last detection timestamp")


class DetectionMetricsResponse(BaseModel):
    """Detection metrics response."""

    timestamp: datetime = Field(..., description="Metrics timestamp")
    total_detections_24h: int = Field(..., description="Total detections in 24 hours")
    detection_rate_per_hour: float = Field(..., description="Average detections per hour")
    false_positive_rate: Optional[float] = Field(None, description="Estimated false positive rate")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    provider_uptime_percent: float = Field(..., description="Provider uptime percentage")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")


# ============================================================================
# WebSocket Message Schemas
# ============================================================================


class DetectionWebSocketMessage(BaseModel):
    """WebSocket message for real-time detections."""

    message_type: str = Field(..., description="Message type: detection, event, status")
    camera_id: str = Field(..., description="Camera ID")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: dict = Field(..., description="Message data (varies by type)")


class WebSocketSubscription(BaseModel):
    """WebSocket subscription request."""

    action: str = Field(..., description="Action: subscribe, unsubscribe, filter")
    camera_id: Optional[str] = Field(None, description="Camera to subscribe to (null = all)")
    event_types: Optional[list[str]] = Field(None, description="Event types to filter")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")


__all__ = [
    "DetectionProviderConfigBase",
    "DetectionProviderConfigCreate",
    "DetectionProviderConfigUpdate",
    "DetectionProviderConfigResponse",
    "BoundingBox",
    "DetectionBase",
    "DetectionResponse",
    "LiveDetectionsResponse",
    "DetectionEventLogResponse",
    "SendFrameRequest",
    "SendFrameResponse",
    "TestDetectionProviderRequest",
    "TestDetectionProviderResponse",
    "LiveDetectionsQuery",
    "DetectionEventsQuery",
    "DetectionStatisticsResponse",
    "DetectionMetricsResponse",
    "DetectionWebSocketMessage",
    "WebSocketSubscription",
]
