"""Camera service for business logic."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.models.camera import Camera, CameraGroup
from app.repositories.camera import (
    CameraGroupRepository,
    CameraHealthRepository,
    CameraRepository,
    CameraSnapshotRepository,
)
from app.schemas.camera import (
    CameraConnectionTestResponse,
    CameraCreate,
    CameraGroupCreate,
    CameraGroupUpdate,
    CameraUpdate,
)

logger = logging.getLogger(__name__)


class CameraGroupService:
    """Service for camera group operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.repo = CameraGroupRepository(db)

    async def create_group(self, request: CameraGroupCreate) -> CameraGroup:
        """Create a new camera group."""
        group_id = str(uuid4())
        return await self.repo.create(
            group_id=group_id,
            name=request.name,
            description=request.description,
            location=request.location,
            order=request.order,
        )

    async def get_group(self, group_id: str) -> CameraGroup:
        """Get camera group by ID."""
        group = await self.repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"Camera group {group_id} not found")
        return group

    async def list_groups(self) -> list[CameraGroup]:
        """List all camera groups."""
        return await self.repo.get_all()

    async def update_group(self, group_id: str, request: CameraGroupUpdate) -> CameraGroup:
        """Update camera group."""
        group = await self.get_group(group_id)
        updated = await self.repo.update(group_id, **request.dict(exclude_unset=True))
        if not updated:
            raise NotFoundError(f"Camera group {group_id} not found")
        return updated

    async def delete_group(self, group_id: str) -> bool:
        """Delete camera group."""
        # Check if group has cameras
        cameras = await CameraRepository(self.db).get_by_group(group_id)
        if cameras:
            raise ValidationError(f"Cannot delete group with {len(cameras)} cameras")

        return await self.repo.delete(group_id)


class CameraService:
    """Service for camera operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.repo = CameraRepository(db)
        self.health_repo = CameraHealthRepository(db)
        self.snapshot_repo = CameraSnapshotRepository(db)

    async def create_camera(self, request: CameraCreate) -> Camera:
        """Create a new camera."""
        # Check for duplicate RTSP URL
        existing = await self.repo.get_by_rtsp_url(request.rtsp_url)
        if existing:
            raise ValidationError("Camera with this RTSP URL already exists")

        camera_id = str(uuid4())
        return await self.repo.create(
            camera_id=camera_id,
            name=request.name,
            rtsp_url=request.rtsp_url,
            username=request.username,
            password=request.password,
            resolution=request.resolution,
            fps=request.fps,
            codec=request.codec,
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            group_id=request.group_id,
            is_active=request.is_active,
            is_primary=request.is_primary,
            enable_recording=request.enable_recording,
            enable_snapshots=request.enable_snapshots,
            enable_detection=request.enable_detection,
            detection_sensitivity=request.detection_sensitivity,
        )

    async def get_camera(self, camera_id: str) -> Camera:
        """Get camera by ID."""
        camera = await self.repo.get_by_id(camera_id)
        if not camera:
            raise NotFoundError(f"Camera {camera_id} not found")
        return camera

    async def list_cameras(self, skip: int = 0, limit: int = 100) -> list[Camera]:
        """List all cameras."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def list_active_cameras(self, skip: int = 0, limit: int = 100) -> list[Camera]:
        """List active cameras."""
        return await self.repo.get_active(skip=skip, limit=limit)

    async def get_cameras_by_group(self, group_id: str) -> list[Camera]:
        """Get cameras in a group."""
        return await self.repo.get_by_group(group_id)

    async def update_camera(self, camera_id: str, request: CameraUpdate) -> Camera:
        """Update camera."""
        camera = await self.get_camera(camera_id)

        # Check for duplicate RTSP URL if URL is being changed
        if request.rtsp_url and request.rtsp_url != camera.rtsp_url:
            existing = await self.repo.get_by_rtsp_url(request.rtsp_url)
            if existing:
                raise ValidationError("Camera with this RTSP URL already exists")

        updated = await self.repo.update(camera_id, **request.dict(exclude_unset=True))
        if not updated:
            raise NotFoundError(f"Camera {camera_id} not found")
        return updated

    async def update_camera_state(self, camera_id: str, status: str,
                                 error_msg: Optional[str] = None) -> Camera:
        """Update camera state."""
        camera = await self.get_camera(camera_id)
        updated = await self.repo.update_status(camera_id, status, error_msg)
        if not updated:
            raise NotFoundError(f"Camera {camera_id} not found")
        return updated

    async def delete_camera(self, camera_id: str) -> bool:
        """Delete camera."""
        await self.get_camera(camera_id)  # Verify exists
        return await self.repo.delete(camera_id)

    async def get_summary(self) -> dict:
        """Get camera system summary."""
        total = await self.repo.count_all()
        active = await self.repo.count_active()
        offline = await self.repo.count_by_status("error")
        recording = len([c for c in await self.repo.get_all() if c.enable_recording])
        detection_enabled = len(await self.repo.get_with_detection_enabled())

        return {
            "total_cameras": total,
            "active_cameras": active,
            "offline_cameras": offline,
            "recording_cameras": recording,
            "detection_enabled": detection_enabled,
            "health_check_status": "healthy" if offline == 0 else "warning" if offline < (total / 2) else "critical",
        }

    async def test_connection(self, camera_id: str, timeout_seconds: int = 10) -> CameraConnectionTestResponse:
        """Test camera connection (placeholder for actual implementation)."""
        camera = await self.get_camera(camera_id)

        try:
            # TODO: Implement actual RTSP connection testing
            # For now, return a mock response
            await self.repo.update_status(camera_id, "live")

            return CameraConnectionTestResponse(
                success=True,
                camera_id=camera_id,
                message=f"Successfully connected to {camera.name}",
                latency_ms=50,
                resolution=camera.resolution,
                fps=camera.fps,
            )
        except Exception as e:
            await self.repo.update_status(camera_id, "error", str(e))
            return CameraConnectionTestResponse(
                success=False,
                camera_id=camera_id,
                message=f"Failed to connect to {camera.name}",
                error=str(e),
            )

    async def capture_snapshot(self, camera_id: str, timeout_seconds: int = 10) -> dict:
        """Capture snapshot from camera (placeholder)."""
        camera = await self.get_camera(camera_id)

        try:
            # TODO: Implement actual snapshot capture using FFmpeg
            snapshot_id = str(uuid4())

            # Create snapshot record
            snapshot = await self.snapshot_repo.create(
                snapshot_id=snapshot_id,
                camera_id=camera_id,
                filename=f"{camera_id}_{datetime.utcnow().timestamp()}.jpg",
                file_size=0,  # Will be set after actual capture
                storage_path=f"snapshots/{camera_id}/{snapshot_id}.jpg",
                mime_type="image/jpeg",
                resolution=camera.resolution,
            )

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "storage_path": snapshot.storage_path,
            }
        except Exception as e:
            logger.error(f"Failed to capture snapshot from camera {camera_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def import_cameras(self, cameras_data: list[dict], group_id: Optional[str] = None) -> dict:
        """Import cameras from data."""
        imported = 0
        skipped = 0
        errors = []

        for idx, camera_data in enumerate(cameras_data):
            try:
                # Check for duplicate RTSP URL
                existing = await self.repo.get_by_rtsp_url(camera_data.get("rtsp_url", ""))
                if existing:
                    skipped += 1
                    continue

                # Create camera
                request = CameraCreate(
                    name=camera_data.get("name", f"Camera {imported + 1}"),
                    rtsp_url=camera_data.get("rtsp_url"),
                    username=camera_data.get("username"),
                    password=camera_data.get("password"),
                    resolution=camera_data.get("resolution", "1920x1080"),
                    fps=camera_data.get("fps", 30),
                    codec=camera_data.get("codec", "h264"),
                    location=camera_data.get("location"),
                    group_id=group_id or camera_data.get("group_id"),
                )
                await self.create_camera(request)
                imported += 1
            except Exception as e:
                errors.append({
                    "row": idx + 1,
                    "error": str(e),
                })

        return {
            "imported_count": imported,
            "skipped_count": skipped,
            "errors": errors,
        }

    async def export_cameras(self, group_id: Optional[str] = None,
                           include_credentials: bool = False) -> list[dict]:
        """Export cameras to data format."""
        if group_id:
            cameras = await self.repo.get_by_group(group_id)
        else:
            cameras = await self.repo.get_all()

        exported = []
        for camera in cameras:
            camera_data = {
                "id": camera.id,
                "name": camera.name,
                "description": camera.description,
                "rtsp_url": camera.rtsp_url,
                "resolution": camera.resolution,
                "fps": camera.fps,
                "codec": camera.codec,
                "location": camera.location,
                "group_id": camera.group_id,
                "is_active": camera.is_active,
                "is_primary": camera.is_primary,
                "enable_recording": camera.enable_recording,
                "enable_snapshots": camera.enable_snapshots,
                "enable_detection": camera.enable_detection,
                "detection_sensitivity": camera.detection_sensitivity,
            }

            if include_credentials:
                camera_data["username"] = camera.username
                camera_data["password"] = camera.password

            exported.append(camera_data)

        return exported
