"""Detection repository for database operations."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection import (
    Detection,
    DetectionEventLog,
    DetectionProcessingQueue,
    DetectionProviderConfig,
)


class DetectionProviderConfigRepository:
    """Repository for detection provider configuration."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, config_id: str, **kwargs) -> DetectionProviderConfig:
        """Create provider config."""
        config = DetectionProviderConfig(id=config_id, **kwargs)
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_by_id(self, config_id: str) -> Optional[DetectionProviderConfig]:
        """Get config by ID."""
        result = await self.db.execute(
            select(DetectionProviderConfig).where(DetectionProviderConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> Optional[DetectionProviderConfig]:
        """Get active provider config."""
        result = await self.db.execute(
            select(DetectionProviderConfig).where(DetectionProviderConfig.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[DetectionProviderConfig]:
        """Get all configs."""
        result = await self.db.execute(select(DetectionProviderConfig))
        return result.scalars().all()

    async def update(self, config_id: str, **kwargs) -> Optional[DetectionProviderConfig]:
        """Update config."""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete(self, config_id: str) -> bool:
        """Delete config."""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()
        return True


class DetectionRepository:
    """Repository for detection records."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, detection_id: str, **kwargs) -> Detection:
        """Create detection record."""
        detection = Detection(id=detection_id, **kwargs)
        self.db.add(detection)
        await self.db.commit()
        await self.db.refresh(detection)
        return detection

    async def get_by_id(self, detection_id: str) -> Optional[Detection]:
        """Get detection by ID."""
        result = await self.db.execute(
            select(Detection).where(Detection.id == detection_id)
        )
        return result.scalar_one_or_none()

    async def get_by_camera(
        self,
        camera_id: str,
        limit: int = 100,
        offset: int = 0,
        unprocessed_only: bool = False,
    ) -> list[Detection]:
        """Get detections for a camera."""
        query = select(Detection).where(Detection.camera_id == camera_id)

        if unprocessed_only:
            query = query.where(Detection.is_processed == False)

        query = query.order_by(Detection.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent(
        self,
        camera_id: Optional[str] = None,
        minutes: int = 5,
        limit: int = 100,
    ) -> list[Detection]:
        """Get recent detections from last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        query = select(Detection).where(Detection.created_at >= cutoff_time)

        if camera_id:
            query = query.where(Detection.camera_id == camera_id)

        query = query.order_by(Detection.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_person(
        self,
        person_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Detection]:
        """Get detections for a person."""
        query = select(Detection).where(Detection.person_id == person_id)
        query = query.order_by(Detection.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_type(
        self,
        detection_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Detection]:
        """Get detections by type."""
        query = select(Detection).where(Detection.detection_type == detection_type)
        query = query.order_by(Detection.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_by_camera(self, camera_id: str) -> int:
        """Count detections for camera."""
        result = await self.db.execute(
            select(Detection).where(Detection.camera_id == camera_id)
        )
        return len(result.scalars().all())

    async def count_recent(
        self,
        camera_id: Optional[str] = None,
        minutes: int = 5,
    ) -> int:
        """Count recent detections."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        query = select(Detection).where(Detection.created_at >= cutoff_time)

        if camera_id:
            query = query.where(Detection.camera_id == camera_id)

        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def update(self, detection_id: str, **kwargs) -> Optional[Detection]:
        """Update detection."""
        detection = await self.get_by_id(detection_id)
        if not detection:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(detection, key):
                setattr(detection, key, value)

        self.db.add(detection)
        await self.db.commit()
        await self.db.refresh(detection)
        return detection

    async def delete(self, detection_id: str) -> bool:
        """Delete detection."""
        detection = await self.get_by_id(detection_id)
        if not detection:
            return False

        await self.db.delete(detection)
        await self.db.commit()
        return True

    async def delete_old_records(self, days: int = 30) -> int:
        """Delete old detections."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(Detection).where(Detection.created_at < cutoff_date)
        )
        old_records = result.scalars().all()

        for record in old_records:
            await self.db.delete(record)

        await self.db.commit()
        return len(old_records)


class DetectionEventLogRepository:
    """Repository for detection event logs."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, event_id: str, **kwargs) -> DetectionEventLog:
        """Create event log."""
        event = DetectionEventLog(id=event_id, **kwargs)
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_by_camera(
        self,
        camera_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DetectionEventLog]:
        """Get events for camera."""
        query = select(DetectionEventLog).where(DetectionEventLog.camera_id == camera_id)
        query = query.order_by(DetectionEventLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_type(
        self,
        event_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DetectionEventLog]:
        """Get events by type."""
        query = select(DetectionEventLog).where(DetectionEventLog.event_type == event_type)
        query = query.order_by(DetectionEventLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_person(
        self,
        person_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DetectionEventLog]:
        """Get events for person."""
        query = select(DetectionEventLog).where(DetectionEventLog.person_id == person_id)
        query = query.order_by(DetectionEventLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent(
        self,
        minutes: int = 5,
        limit: int = 100,
    ) -> list[DetectionEventLog]:
        """Get recent events."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        query = select(DetectionEventLog).where(DetectionEventLog.created_at >= cutoff_time)
        query = query.order_by(DetectionEventLog.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_old_records(self, days: int = 90) -> int:
        """Delete old event logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(DetectionEventLog).where(DetectionEventLog.created_at < cutoff_date)
        )
        old_records = result.scalars().all()

        for record in old_records:
            await self.db.delete(record)

        await self.db.commit()
        return len(old_records)


class DetectionProcessingQueueRepository:
    """Repository for detection processing queue."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def enqueue(self, queue_id: str, **kwargs) -> DetectionProcessingQueue:
        """Add frame to processing queue."""
        queue_item = DetectionProcessingQueue(id=queue_id, **kwargs)
        self.db.add(queue_item)
        await self.db.commit()
        await self.db.refresh(queue_item)
        return queue_item

    async def get_pending(self, limit: int = 10) -> list[DetectionProcessingQueue]:
        """Get pending frames for processing."""
        query = select(DetectionProcessingQueue).where(
            DetectionProcessingQueue.status == "pending"
        )
        query = query.order_by(DetectionProcessingQueue.priority.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, queue_id: str) -> Optional[DetectionProcessingQueue]:
        """Get queue item by ID."""
        result = await self.db.execute(
            select(DetectionProcessingQueue).where(DetectionProcessingQueue.id == queue_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        queue_id: str,
        status: str,
        **kwargs,
    ) -> Optional[DetectionProcessingQueue]:
        """Update queue item status."""
        item = await self.get_by_id(queue_id)
        if not item:
            return None

        item.status = status
        for key, value in kwargs.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def mark_completed(
        self,
        queue_id: str,
        detections_count: int = 0,
        processing_time_ms: int = 0,
    ) -> Optional[DetectionProcessingQueue]:
        """Mark queue item as completed."""
        return await self.update_status(
            queue_id,
            "completed",
            detections_count=detections_count,
            processing_time_ms=processing_time_ms,
        )

    async def mark_failed(
        self,
        queue_id: str,
        error_message: str,
    ) -> Optional[DetectionProcessingQueue]:
        """Mark queue item as failed."""
        item = await self.get_by_id(queue_id)
        if not item:
            return None

        if item.retry_count < item.max_retries:
            # Retry
            item.status = "pending"
            item.retry_count += 1
        else:
            # Give up
            item.status = "failed"

        item.error_message = error_message
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def cleanup_old_records(self, days: int = 7) -> int:
        """Delete old queue records."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(DetectionProcessingQueue).where(DetectionProcessingQueue.created_at < cutoff_date)
        )
        old_records = result.scalars().all()

        for record in old_records:
            await self.db.delete(record)

        await self.db.commit()
        return len(old_records)

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        result_pending = await self.db.execute(
            select(DetectionProcessingQueue).where(DetectionProcessingQueue.status == "pending")
        )
        pending = len(result_pending.scalars().all())

        result_processing = await self.db.execute(
            select(DetectionProcessingQueue).where(
                DetectionProcessingQueue.status == "processing"
            )
        )
        processing = len(result_processing.scalars().all())

        result_completed = await self.db.execute(
            select(DetectionProcessingQueue).where(
                DetectionProcessingQueue.status == "completed"
            )
        )
        completed = len(result_completed.scalars().all())

        result_failed = await self.db.execute(
            select(DetectionProcessingQueue).where(DetectionProcessingQueue.status == "failed")
        )
        failed = len(result_failed.scalars().all())

        return {
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total": pending + processing + completed + failed,
        }
