"""Detection service for business logic."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.redis import cache_service
from app.models.detection import (
    Detection,
    DetectionEventLog,
    DetectionProcessingQueue,
    DetectionProviderConfig,
)
from app.repositories.detection import (
    DetectionEventLogRepository,
    DetectionProcessingQueueRepository,
    DetectionProviderConfigRepository,
    DetectionRepository,
)
from app.schemas.detection import (
    DetectionProviderConfigCreate,
    DetectionProviderConfigUpdate,
    DetectionResponse,
    TestDetectionProviderResponse,
)
from app.services.detection_provider import DetectionProviderService

logger = logging.getLogger(__name__)


class DetectionService:
    """Service for detection operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.repo = DetectionRepository(db)
        self.event_repo = DetectionEventLogRepository(db)
        self.queue_repo = DetectionProcessingQueueRepository(db)
        self.config_repo = DetectionProviderConfigRepository(db)
        self.provider_service = DetectionProviderService()
        self.cache = cache_service

    # =========================================================================
    # Provider Configuration Methods
    # =========================================================================

    async def get_provider_config(self, config_id: Optional[str] = None) -> DetectionProviderConfig:
        """Get detection provider configuration."""
        if config_id:
            config = await self.config_repo.get_by_id(config_id)
            if not config:
                raise NotFoundError(f"Provider config {config_id} not found")
            return config
        else:
            # Get active config
            config = await self.config_repo.get_active()
            if not config:
                raise NotFoundError("No active detection provider configured")
            return config

    async def create_provider_config(
        self,
        request: DetectionProviderConfigCreate,
    ) -> DetectionProviderConfig:
        """Create a new detection provider configuration."""
        config_id = str(uuid4())
        config = await self.config_repo.create(
            config_id=config_id,
            provider_name=request.provider_name,
            provider_type=request.provider_type,
            endpoint_url=request.endpoint_url,
            api_key=request.api_key,
            api_secret=request.api_secret,
            timeout_seconds=request.timeout_seconds,
            max_faces_per_frame=request.max_faces_per_frame,
            confidence_threshold=request.confidence_threshold,
            enable_person_detection=request.enable_person_detection,
            enable_face_detection=request.enable_face_detection,
            enable_face_encoding=request.enable_face_encoding,
            is_active=request.is_active,
            test_status="untested",
        )
        logger.info(f"Created detection provider config: {config_id}")
        return config

    async def update_provider_config(
        self,
        config_id: str,
        request: DetectionProviderConfigUpdate,
    ) -> DetectionProviderConfig:
        """Update detection provider configuration."""
        config = await self.get_provider_config(config_id)

        updated = await self.config_repo.update(
            config_id,
            **request.dict(exclude_unset=True),
        )
        if not updated:
            raise NotFoundError(f"Provider config {config_id} not found")

        logger.info(f"Updated detection provider config: {config_id}")
        return updated

    async def delete_provider_config(self, config_id: str) -> bool:
        """Delete detection provider configuration."""
        await self.get_provider_config(config_id)  # Verify exists
        result = await self.config_repo.delete(config_id)
        if result:
            logger.info(f"Deleted detection provider config: {config_id}")
        return result

    async def list_provider_configs(self) -> list[DetectionProviderConfig]:
        """List all provider configurations."""
        return await self.config_repo.get_all()

    # =========================================================================
    # Provider Testing Methods
    # =========================================================================

    async def test_provider_connection(
        self,
        config_id: Optional[str] = None,
        timeout_seconds: int = 10,
    ) -> TestDetectionProviderResponse:
        """Test detection provider connection."""
        try:
            config = await self.get_provider_config(config_id)

            # Test the connection
            result = await self.provider_service.test_provider_connection(
                provider_endpoint=config.endpoint_url,
                api_key=config.api_key,
                timeout=timeout_seconds,
            )

            # Update test status
            if result.success:
                test_status = "success"
                last_error = None
            else:
                test_status = "failed"
                last_error = result.error

            await self.config_repo.update(
                config.id,
                test_status=test_status,
                last_tested=datetime.utcnow(),
                last_error=last_error,
            )

            logger.info(f"Provider test completed: {config.provider_name} - {test_status}")
            return result

        except Exception as e:
            logger.error(f"Error testing provider connection: {e}")
            raise ValidationError(f"Provider test failed: {str(e)}")

    # =========================================================================
    # Detection Methods
    # =========================================================================

    async def send_frame_for_detection(
        self,
        camera_id: str,
        frame_data: bytes,
        frame_number: Optional[int] = None,
        frame_timestamp: Optional[datetime] = None,
    ) -> dict:
        """Send frame to detection provider."""
        try:
            # Get active provider config
            config = await self.get_provider_config()

            start_time = datetime.utcnow()

            # Send frame to provider
            provider_response = await self.provider_service.send_frame_to_provider(
                provider_endpoint=config.endpoint_url,
                frame_data=frame_data,
                api_key=config.api_key,
                timeout=config.timeout_seconds,
                max_faces=config.max_faces_per_frame,
                confidence_threshold=config.confidence_threshold,
            )

            # Parse provider response
            detections = self.provider_service.parse_provider_response(
                camera_id=camera_id,
                provider_response=provider_response,
            )

            # Filter by confidence threshold
            filtered_detections = [
                d for d in detections
                if d.confidence >= config.confidence_threshold
            ]

            # Store detections in database
            stored_detections = []
            for detection in filtered_detections:
                db_detection = await self.repo.create(
                    detection_id=detection.id,
                    camera_id=camera_id,
                    detection_type=detection.detection_type,
                    confidence=detection.confidence,
                    bbox_x=detection.bbox.x,
                    bbox_y=detection.bbox.y,
                    bbox_width=detection.bbox.width,
                    bbox_height=detection.bbox.height,
                    person_name=detection.person_name,
                    person_id=detection.person_id,
                    face_encoding=detection.face_encoding,
                    frame_number=frame_number,
                    frame_timestamp=frame_timestamp or datetime.utcnow(),
                    is_processed=True,
                    processing_status="completed",
                )
                stored_detections.append(db_detection)

            # Cache live detections
            detection_dicts = [
                {
                    "id": d.id,
                    "detection_type": d.detection_type,
                    "confidence": d.confidence,
                    "bbox": {
                        "x": d.bbox_x,
                        "y": d.bbox_y,
                        "width": d.bbox_width,
                        "height": d.bbox_height,
                    },
                    "person_name": d.person_name,
                    "person_id": d.person_id,
                }
                for d in stored_detections
            ]
            await self.cache.cache_live_detections(camera_id, detection_dicts)

            # Create event log
            await self.create_event_log(
                detection_id=None,
                camera_id=camera_id,
                event_type="detection_completed",
                severity="info",
                message=f"Detected {len(filtered_detections)} objects",
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            logger.info(
                f"Frame processed from camera {camera_id}: "
                f"{len(filtered_detections)} detections in {processing_time:.2f}ms"
            )

            return {
                "success": True,
                "camera_id": camera_id,
                "detection_count": len(filtered_detections),
                "detections": stored_detections,
                "processing_time_ms": int(processing_time),
            }

        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            await self.create_event_log(
                detection_id=None,
                camera_id=camera_id,
                event_type="detection_failed",
                severity="error",
                message=f"Detection failed: {str(e)}",
            )
            raise ValidationError(f"Failed to process frame: {str(e)}")

    async def get_live_detections(
        self,
        camera_id: Optional[str] = None,
        detection_type: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 100,
        offset: int = 0,
        use_cache: bool = True,
    ) -> dict:
        """Get live detections with optional caching."""
        # Try cache first
        if use_cache and camera_id:
            cached = await self.cache.get_cached_live_detections(camera_id)
            if cached:
                return {
                    "detections": cached.get("detections", []),
                    "total_detections": cached.get("count", 0),
                    "last_updated": cached.get("timestamp"),
                    "cache_hit": True,
                }

        # Get from database
        if camera_id:
            detections = await self.repo.get_by_camera(
                camera_id,
                limit=limit,
                offset=offset,
                unprocessed_only=False,
            )
        else:
            # Get recent detections
            detections = await self.repo.get_recent(
                camera_id=camera_id,
                limit=limit,
            )

        # Filter by detection type
        if detection_type:
            detections = [d for d in detections if d.detection_type == detection_type]

        # Filter by confidence
        detections = [d for d in detections if d.confidence >= min_confidence]

        # Cache if camera_id provided
        if use_cache and camera_id and detections:
            detection_dicts = [
                {
                    "id": d.id,
                    "detection_type": d.detection_type,
                    "confidence": d.confidence,
                    "bbox": {
                        "x": d.bbox_x,
                        "y": d.bbox_y,
                        "width": d.bbox_width,
                        "height": d.bbox_height,
                    },
                    "person_name": d.person_name,
                    "person_id": d.person_id,
                }
                for d in detections
            ]
            await self.cache.cache_live_detections(camera_id, detection_dicts)

        return {
            "detections": detections,
            "total_detections": len(detections),
            "last_updated": datetime.utcnow(),
            "cache_hit": False,
        }

    async def get_detection(self, detection_id: str) -> Detection:
        """Get detection by ID."""
        detection = await self.repo.get_by_id(detection_id)
        if not detection:
            raise NotFoundError(f"Detection {detection_id} not found")
        return detection

    async def get_recent_detections(
        self,
        camera_id: Optional[str] = None,
        minutes: int = 5,
        limit: int = 100,
    ) -> list[Detection]:
        """Get recent detections from last N minutes."""
        return await self.repo.get_recent(
            camera_id=camera_id,
            minutes=minutes,
            limit=limit,
        )

    async def get_detections_by_person(
        self,
        person_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Detection]:
        """Get detections for a person."""
        return await self.repo.get_by_person(
            person_id=person_id,
            limit=limit,
            offset=offset,
        )

    # =========================================================================
    # Event Log Methods
    # =========================================================================

    async def create_event_log(
        self,
        detection_id: Optional[str],
        camera_id: str,
        event_type: str,
        severity: str,
        message: str,
        person_id: Optional[str] = None,
        person_name: Optional[str] = None,
        confidence_score: Optional[float] = None,
        action_taken: Optional[str] = None,
    ) -> DetectionEventLog:
        """Create an event log entry."""
        event_id = str(uuid4())
        event = await self.event_repo.create(
            event_id=event_id,
            detection_id=detection_id,
            camera_id=camera_id,
            event_type=event_type,
            severity=severity,
            message=message,
            person_id=person_id,
            person_name=person_name,
            confidence_score=confidence_score,
            action_taken=action_taken,
            action_timestamp=None,
            source_system="detection_service",
        )
        logger.info(f"Created event log: {event_id} - {event_type}")
        return event

    async def get_detection_events(
        self,
        camera_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        person_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get detection events with filtering."""
        # Get events by camera if specified
        if camera_id:
            events = await self.event_repo.get_by_camera(
                camera_id=camera_id,
                limit=limit + offset,
                offset=0,
            )
        else:
            # Get recent events
            events = await self.event_repo.get_recent(limit=limit + offset)

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Filter by severity
        if severity:
            events = [e for e in events if e.severity == severity]

        # Filter by person ID
        if person_id:
            events = [e for e in events if e.person_id == person_id]

        # Filter by time range
        if start_time:
            events = [e for e in events if e.createdAt >= start_time]
        if end_time:
            events = [e for e in events if e.createdAt <= end_time]

        # Apply pagination
        events = events[offset : offset + limit]

        return {
            "events": events,
            "total_events": len(events),
            "camera_id": camera_id,
        }

    # =========================================================================
    # Statistics Methods
    # =========================================================================

    async def get_detection_statistics(
        self,
        camera_id: Optional[str] = None,
    ) -> dict:
        """Get detection statistics."""
        # Try cache first
        cache_key = f"camera_{camera_id}" if camera_id else "all_cameras"
        cached_stats = await self.cache.get_cached_statistics(cache_key)
        if cached_stats:
            return cached_stats

        now = datetime.utcnow()

        # Count total detections
        total_detections = await self.repo.count_by_camera(camera_id) if camera_id else 0

        # Count detections today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_today = await self.repo.get_recent(camera_id=camera_id, minutes=int((now - today_start).total_seconds() / 60))
        detections_today = len(recent_today)

        # Count detections this hour
        recent_hour = await self.repo.get_recent(camera_id=camera_id, minutes=60)
        detections_this_hour = len(recent_hour)

        # Calculate average confidence
        if recent_today:
            average_confidence = sum(d.confidence for d in recent_today) / len(recent_today)
        else:
            average_confidence = 0.0

        # Get most detected person
        if recent_today:
            person_counts = {}
            for d in recent_today:
                if d.person_id:
                    person_counts[d.person_id] = person_counts.get(d.person_id, 0) + 1
            most_detected_person = max(person_counts, key=person_counts.get) if person_counts else None
        else:
            most_detected_person = None

        # Get detection type breakdown
        if recent_today:
            type_counts = {}
            for d in recent_today:
                type_counts[d.detection_type] = type_counts.get(d.detection_type, 0) + 1
            detection_types = type_counts
        else:
            detection_types = {}

        # Get number of active cameras
        cameras_active = 1 if camera_id else 0

        # Get last detection timestamp
        recent = await self.repo.get_recent(camera_id=camera_id, limit=1)
        last_detection_timestamp = recent[0].createdAt if recent else None

        stats = {
            "total_detections": total_detections,
            "detections_today": detections_today,
            "detections_this_hour": detections_this_hour,
            "average_confidence": round(average_confidence, 3),
            "most_detected_person": most_detected_person,
            "detection_types": detection_types,
            "cameras_active": cameras_active,
            "last_detection_timestamp": last_detection_timestamp,
        }

        # Cache statistics
        await self.cache.cache_detection_statistics(cache_key, stats)

        return stats

    # =========================================================================
    # Queue Methods
    # =========================================================================

    async def enqueue_frame(
        self,
        camera_id: str,
        frame_data: bytes,
        priority: int = 5,
        frame_number: Optional[int] = None,
        frame_timestamp: Optional[datetime] = None,
    ) -> DetectionProcessingQueue:
        """Add frame to processing queue."""
        queue_id = str(uuid4())
        queue_item = await self.queue_repo.enqueue(
            queue_id=queue_id,
            camera_id=camera_id,
            frame_data=frame_data,
            priority=priority,
            frame_number=frame_number,
            frame_timestamp=frame_timestamp or datetime.utcnow(),
            status="pending",
            retry_count=0,
            max_retries=3,
        )
        logger.info(f"Queued frame from camera {camera_id}: {queue_id}")
        return queue_item

    async def get_pending_frames(self, limit: int = 10) -> list[DetectionProcessingQueue]:
        """Get pending frames for processing."""
        return await self.queue_repo.get_pending(limit=limit)

    async def mark_frame_completed(
        self,
        queue_id: str,
        detections_count: int = 0,
        processing_time_ms: int = 0,
    ) -> DetectionProcessingQueue:
        """Mark frame as completed."""
        result = await self.queue_repo.mark_completed(
            queue_id=queue_id,
            detections_count=detections_count,
            processing_time_ms=processing_time_ms,
        )
        if not result:
            raise NotFoundError(f"Queue item {queue_id} not found")
        logger.info(f"Frame completed: {queue_id}")
        return result

    async def mark_frame_failed(
        self,
        queue_id: str,
        error_message: str,
    ) -> DetectionProcessingQueue:
        """Mark frame as failed (with retry logic)."""
        result = await self.queue_repo.mark_failed(
            queue_id=queue_id,
            error_message=error_message,
        )
        if not result:
            raise NotFoundError(f"Queue item {queue_id} not found")

        if result.status == "pending":
            logger.warning(f"Frame retry queued: {queue_id} (attempt {result.retry_count})")
        else:
            logger.error(f"Frame processing failed: {queue_id} - {error_message}")

        return result

    async def get_queue_stats(self) -> dict:
        """Get processing queue statistics."""
        return await self.queue_repo.get_queue_stats()

    # =========================================================================
    # Cleanup Methods
    # =========================================================================

    async def cleanup_old_detections(self, days: int = 30) -> int:
        """Delete old detection records."""
        count = await self.repo.delete_old_records(days=days)
        logger.info(f"Deleted {count} old detection records (older than {days} days)")
        return count

    async def cleanup_old_events(self, days: int = 90) -> int:
        """Delete old event logs."""
        count = await self.event_repo.delete_old_records(days=days)
        logger.info(f"Deleted {count} old event logs (older than {days} days)")
        return count

    async def cleanup_old_queue_records(self, days: int = 7) -> int:
        """Delete old queue records."""
        count = await self.queue_repo.cleanup_old_records(days=days)
        logger.info(f"Deleted {count} old queue records (older than {days} days)")
        return count

    # =========================================================================
    # Summary Methods
    # =========================================================================

    async def get_detection_summary(self) -> dict:
        """Get detection system summary."""
        config = await self.config_repo.get_active()
        queue_stats = await self.queue_repo.get_queue_stats()
        stats = await self.get_detection_statistics()

        return {
            "provider_configured": config is not None,
            "provider_name": config.provider_name if config else None,
            "provider_active": config.is_active if config else False,
            "provider_test_status": config.test_status if config else "not_configured",
            "queue_stats": queue_stats,
            "detection_stats": stats,
        }
