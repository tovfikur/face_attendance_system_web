"""Camera repository for database operations."""

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera, CameraGroup, CameraHealth, CameraSnapshot


class CameraGroupRepository:
    """Repository for camera group operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, group_id: str, name: str, description: Optional[str] = None,
                     location: Optional[str] = None, order: int = 0) -> CameraGroup:
        """Create a new camera group."""
        group = CameraGroup(
            id=group_id,
            name=name,
            description=description,
            location=location,
            order=order,
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_by_id(self, group_id: str) -> Optional[CameraGroup]:
        """Get group by ID."""
        result = await self.db.execute(select(CameraGroup).where(CameraGroup.id == group_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[CameraGroup]:
        """Get all groups."""
        result = await self.db.execute(select(CameraGroup).order_by(CameraGroup.order, CameraGroup.name))
        return result.scalars().all()

    async def update(self, group_id: str, **kwargs) -> Optional[CameraGroup]:
        """Update group."""
        group = await self.get_by_id(group_id)
        if not group:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(group, key):
                setattr(group, key, value)

        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete(self, group_id: str) -> bool:
        """Delete group."""
        group = await self.get_by_id(group_id)
        if not group:
            return False

        await self.db.delete(group)
        await self.db.commit()
        return True


class CameraRepository:
    """Repository for camera operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, camera_id: str, name: str, rtsp_url: str, **kwargs) -> Camera:
        """Create a new camera."""
        camera = Camera(
            id=camera_id,
            name=name,
            rtsp_url=rtsp_url,
            **kwargs
        )
        self.db.add(camera)
        await self.db.commit()
        await self.db.refresh(camera)
        return camera

    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID."""
        result = await self.db.execute(select(Camera).where(Camera.id == camera_id))
        return result.scalar_one_or_none()

    async def get_by_rtsp_url(self, rtsp_url: str) -> Optional[Camera]:
        """Get camera by RTSP URL."""
        result = await self.db.execute(select(Camera).where(Camera.rtsp_url == rtsp_url))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Camera]:
        """Get all cameras."""
        result = await self.db.execute(
            select(Camera).order_by(Camera.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_active(self, skip: int = 0, limit: int = 100) -> list[Camera]:
        """Get all active cameras."""
        result = await self.db.execute(
            select(Camera).where(Camera.is_active == True).order_by(Camera.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_group(self, group_id: str) -> list[Camera]:
        """Get all cameras in a group."""
        result = await self.db.execute(
            select(Camera).where(Camera.group_id == group_id).order_by(Camera.name)
        )
        return result.scalars().all()

    async def get_by_status(self, status: str) -> list[Camera]:
        """Get cameras by status."""
        result = await self.db.execute(
            select(Camera).where(Camera.status == status).order_by(Camera.created_at.desc())
        )
        return result.scalars().all()

    async def get_with_detection_enabled(self) -> list[Camera]:
        """Get cameras with detection enabled."""
        result = await self.db.execute(
            select(Camera).where(and_(Camera.is_active == True, Camera.enable_detection == True))
        )
        return result.scalars().all()

    async def count_all(self) -> int:
        """Count total cameras."""
        result = await self.db.execute(select(Camera))
        return len(result.scalars().all())

    async def count_active(self) -> int:
        """Count active cameras."""
        result = await self.db.execute(select(Camera).where(Camera.is_active == True))
        return len(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        """Count cameras by status."""
        result = await self.db.execute(select(Camera).where(Camera.status == status))
        return len(result.scalars().all())

    async def update(self, camera_id: str, **kwargs) -> Optional[Camera]:
        """Update camera."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(camera, key):
                setattr(camera, key, value)

        self.db.add(camera)
        await self.db.commit()
        await self.db.refresh(camera)
        return camera

    async def update_status(self, camera_id: str, status: str, error_msg: Optional[str] = None) -> Optional[Camera]:
        """Update camera status."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None

        camera.status = status
        if error_msg:
            camera.last_error = error_msg

        self.db.add(camera)
        await self.db.commit()
        await self.db.refresh(camera)
        return camera

    async def delete(self, camera_id: str) -> bool:
        """Delete camera."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return False

        await self.db.delete(camera)
        await self.db.commit()
        return True


class CameraHealthRepository:
    """Repository for camera health operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, health_id: str, camera_id: str, **kwargs) -> CameraHealth:
        """Create health record."""
        health = CameraHealth(
            id=health_id,
            camera_id=camera_id,
            **kwargs
        )
        self.db.add(health)
        await self.db.commit()
        await self.db.refresh(health)
        return health

    async def get_latest(self, camera_id: str) -> Optional[CameraHealth]:
        """Get latest health record for camera."""
        result = await self.db.execute(
            select(CameraHealth)
            .where(CameraHealth.camera_id == camera_id)
            .order_by(CameraHealth.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, camera_id: str, limit: int = 100) -> list[CameraHealth]:
        """Get health history for camera."""
        result = await self.db.execute(
            select(CameraHealth)
            .where(CameraHealth.camera_id == camera_id)
            .order_by(CameraHealth.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_old_records(self, days: int = 30) -> int:
        """Delete old health records (for cleanup)."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(CameraHealth).where(CameraHealth.created_at < cutoff_date)
        )
        old_records = result.scalars().all()

        for record in old_records:
            await self.db.delete(record)

        await self.db.commit()
        return len(old_records)


class CameraSnapshotRepository:
    """Repository for camera snapshot operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, snapshot_id: str, camera_id: str, **kwargs) -> CameraSnapshot:
        """Create snapshot record."""
        snapshot = CameraSnapshot(
            id=snapshot_id,
            camera_id=camera_id,
            **kwargs
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_by_id(self, snapshot_id: str) -> Optional[CameraSnapshot]:
        """Get snapshot by ID."""
        result = await self.db.execute(select(CameraSnapshot).where(CameraSnapshot.id == snapshot_id))
        return result.scalar_one_or_none()

    async def get_latest(self, camera_id: str) -> Optional[CameraSnapshot]:
        """Get latest snapshot for camera."""
        result = await self.db.execute(
            select(CameraSnapshot)
            .where(CameraSnapshot.camera_id == camera_id)
            .order_by(CameraSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_camera(self, camera_id: str, limit: int = 100, archived: bool = False) -> list[CameraSnapshot]:
        """Get snapshots for camera."""
        result = await self.db.execute(
            select(CameraSnapshot)
            .where(and_(CameraSnapshot.camera_id == camera_id, CameraSnapshot.is_archived == archived))
            .order_by(CameraSnapshot.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, snapshot_id: str, **kwargs) -> Optional[CameraSnapshot]:
        """Update snapshot."""
        snapshot = await self.get_by_id(snapshot_id)
        if not snapshot:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(snapshot, key):
                setattr(snapshot, key, value)

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def delete(self, snapshot_id: str) -> bool:
        """Delete snapshot."""
        snapshot = await self.get_by_id(snapshot_id)
        if not snapshot:
            return False

        await self.db.delete(snapshot)
        await self.db.commit()
        return True

    async def delete_expired(self) -> int:
        """Delete expired snapshots."""
        from datetime import datetime

        result = await self.db.execute(
            select(CameraSnapshot).where(
                and_(
                    CameraSnapshot.expiry_date.isnot(None),
                    CameraSnapshot.expiry_date < datetime.utcnow()
                )
            )
        )
        expired = result.scalars().all()

        for snapshot in expired:
            await self.db.delete(snapshot)

        await self.db.commit()
        return len(expired)
