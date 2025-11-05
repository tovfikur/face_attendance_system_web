"""Camera management endpoints."""

import base64
import json
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.camera import (
    CameraConnectionTestRequest,
    CameraConnectionTestResponse,
    CameraCreate,
    CameraExportRequest,
    CameraExportResponse,
    CameraGroupCreate,
    CameraGroupResponse,
    CameraGroupUpdate,
    CameraImportRequest,
    CameraImportResponse,
    CameraResponse,
    CameraSnapshotRequest,
    CameraSnapshotResponse,
    CameraSummaryResponse,
    CameraStateUpdate,
    CameraUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.services.camera_service import CameraGroupService, CameraService
from app.services.ffmpeg_service import FFmpegService
from app.services.storage_service import StorageService

router = APIRouter(tags=["Cameras"])
logger = logging.getLogger(__name__)

# Helper functions
async def get_camera_service(db: AsyncSession = Depends(get_db)) -> CameraService:
    """Get camera service."""
    return CameraService(db)

async def get_camera_group_service(db: AsyncSession = Depends(get_db)) -> CameraGroupService:
    """Get camera group service."""
    return CameraGroupService(db)


# ============================================================================
# Camera Group Endpoints
# ============================================================================

@router.get("/groups", response_model=SuccessResponse[list[CameraGroupResponse]])
async def list_camera_groups(
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraGroupService = Depends(get_camera_group_service),
) -> SuccessResponse[list[CameraGroupResponse]]:
    """List all camera groups."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view cameras",
        )

    groups = await service.list_groups()
    return SuccessResponse(
        data=[
            CameraGroupResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                location=g.location,
                order=g.order,
                createdAt=g.created_at,
                updatedAt=g.updated_at,
            )
            for g in groups
        ]
    )


@router.post("/groups", response_model=SuccessResponse[CameraGroupResponse], status_code=status.HTTP_201_CREATED)
async def create_camera_group(
    request: CameraGroupCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraGroupService = Depends(get_camera_group_service),
) -> SuccessResponse[CameraGroupResponse]:
    """Create a new camera group."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    group = await service.create_group(request)
    return SuccessResponse(
        data=CameraGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            location=group.location,
            order=group.order,
            createdAt=group.created_at,
            updatedAt=group.updated_at,
        )
    )


# ============================================================================
# Camera CRUD Endpoints
# ============================================================================

@router.get("", response_model=PaginatedResponse[CameraResponse])
async def list_cameras(
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    group_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    active_only: bool = Query(False),
) -> PaginatedResponse[CameraResponse]:
    """List all cameras with pagination and filtering."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view cameras",
        )

    skip = (page - 1) * page_size

    if active_only:
        cameras = await service.list_active_cameras(skip=skip, limit=page_size)
        total = await service.repo.count_active()
    elif group_id:
        cameras = await service.get_cameras_by_group(group_id)
        cameras = cameras[skip : skip + page_size]
        total = len(await service.get_cameras_by_group(group_id))
    elif status:
        cameras = await service.repo.get_by_status(status)
        cameras = cameras[skip : skip + page_size]
        total = await service.repo.count_by_status(status)
    else:
        cameras = await service.list_cameras(skip=skip, limit=page_size)
        total = await service.repo.count_all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=[
            CameraResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                rtsp_url=c.rtsp_url,
                username=c.username,
                password=c.password,
                resolution=c.resolution,
                fps=c.fps,
                codec=c.codec,
                location=c.location,
                latitude=c.latitude,
                longitude=c.longitude,
                group_id=c.group_id,
                is_active=c.is_active,
                is_primary=c.is_primary,
                enable_recording=c.enable_recording,
                enable_snapshots=c.enable_snapshots,
                enable_detection=c.enable_detection,
                detection_sensitivity=c.detection_sensitivity,
                status=c.status,
                last_connected=c.last_connected,
                last_error=c.last_error,
                connection_retries=c.connection_retries,
                createdAt=c.created_at,
                updatedAt=c.updated_at,
            )
            for c in cameras
        ],
        meta=PaginationMeta(page=page, pageSize=page_size, total=total, totalPages=total_pages),
    )


@router.post("", response_model=SuccessResponse[CameraResponse], status_code=status.HTTP_201_CREATED)
async def create_camera(
    request: CameraCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraResponse]:
    """Create a new camera."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    camera = await service.create_camera(request)
    return SuccessResponse(
        data=CameraResponse(
            id=camera.id,
            name=camera.name,
            description=camera.description,
            rtsp_url=camera.rtsp_url,
            username=camera.username,
            password=camera.password,
            resolution=camera.resolution,
            fps=camera.fps,
            codec=camera.codec,
            location=camera.location,
            latitude=camera.latitude,
            longitude=camera.longitude,
            group_id=camera.group_id,
            is_active=camera.is_active,
            is_primary=camera.is_primary,
            enable_recording=camera.enable_recording,
            enable_snapshots=camera.enable_snapshots,
            enable_detection=camera.enable_detection,
            detection_sensitivity=camera.detection_sensitivity,
            status=camera.status,
            last_connected=camera.last_connected,
            last_error=camera.last_error,
            connection_retries=camera.connection_retries,
            createdAt=camera.created_at,
            updatedAt=camera.updated_at,
        ),
        meta={"created": True},
    )


@router.get("/{camera_id}", response_model=SuccessResponse[CameraResponse])
async def get_camera(
    camera_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraResponse]:
    """Get a specific camera."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view cameras",
        )

    camera = await service.get_camera(camera_id)
    return SuccessResponse(
        data=CameraResponse(
            id=camera.id,
            name=camera.name,
            description=camera.description,
            rtsp_url=camera.rtsp_url,
            username=camera.username,
            password=camera.password,
            resolution=camera.resolution,
            fps=camera.fps,
            codec=camera.codec,
            location=camera.location,
            latitude=camera.latitude,
            longitude=camera.longitude,
            group_id=camera.group_id,
            is_active=camera.is_active,
            is_primary=camera.is_primary,
            enable_recording=camera.enable_recording,
            enable_snapshots=camera.enable_snapshots,
            enable_detection=camera.enable_detection,
            detection_sensitivity=camera.detection_sensitivity,
            status=camera.status,
            last_connected=camera.last_connected,
            last_error=camera.last_error,
            connection_retries=camera.connection_retries,
            createdAt=camera.created_at,
            updatedAt=camera.updated_at,
        )
    )


@router.put("/{camera_id}", response_model=SuccessResponse[CameraResponse])
async def update_camera(
    camera_id: str,
    request: CameraUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraResponse]:
    """Update a camera."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    camera = await service.update_camera(camera_id, request)
    return SuccessResponse(
        data=CameraResponse(
            id=camera.id,
            name=camera.name,
            description=camera.description,
            rtsp_url=camera.rtsp_url,
            username=camera.username,
            password=camera.password,
            resolution=camera.resolution,
            fps=camera.fps,
            codec=camera.codec,
            location=camera.location,
            latitude=camera.latitude,
            longitude=camera.longitude,
            group_id=camera.group_id,
            is_active=camera.is_active,
            is_primary=camera.is_primary,
            enable_recording=camera.enable_recording,
            enable_snapshots=camera.enable_snapshots,
            enable_detection=camera.enable_detection,
            detection_sensitivity=camera.detection_sensitivity,
            status=camera.status,
            last_connected=camera.last_connected,
            last_error=camera.last_error,
            connection_retries=camera.connection_retries,
            createdAt=camera.created_at,
            updatedAt=camera.updated_at,
        )
    )


@router.patch("/{camera_id}/state", response_model=SuccessResponse[CameraResponse])
async def update_camera_state(
    camera_id: str,
    request: CameraStateUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraResponse]:
    """Update camera state (status, active status)."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    # Use the update endpoint for partial updates
    update_data = request.dict(exclude_unset=True)
    camera = await service.update_camera(camera_id, CameraUpdate(**update_data))

    return SuccessResponse(
        data=CameraResponse(
            id=camera.id,
            name=camera.name,
            description=camera.description,
            rtsp_url=camera.rtsp_url,
            username=camera.username,
            password=camera.password,
            resolution=camera.resolution,
            fps=camera.fps,
            codec=camera.codec,
            location=camera.location,
            latitude=camera.latitude,
            longitude=camera.longitude,
            group_id=camera.group_id,
            is_active=camera.is_active,
            is_primary=camera.is_primary,
            enable_recording=camera.enable_recording,
            enable_snapshots=camera.enable_snapshots,
            enable_detection=camera.enable_detection,
            detection_sensitivity=camera.detection_sensitivity,
            status=camera.status,
            last_connected=camera.last_connected,
            last_error=camera.last_error,
            connection_retries=camera.connection_retries,
            createdAt=camera.created_at,
            updatedAt=camera.updated_at,
        )
    )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> None:
    """Delete a camera."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    await service.delete_camera(camera_id)


# ============================================================================
# Camera Operation Endpoints
# ============================================================================

@router.post("/{camera_id}/test-connection", response_model=SuccessResponse[CameraConnectionTestResponse])
async def test_camera_connection(
    camera_id: str,
    request: CameraConnectionTestRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraConnectionTestResponse]:
    """Test camera connection."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access cameras",
        )

    result = await service.test_connection(camera_id, request.timeout_seconds)
    return SuccessResponse(data=result)


@router.post("/{camera_id}/snapshot", response_model=SuccessResponse[CameraSnapshotResponse])
async def capture_camera_snapshot(
    camera_id: str,
    request: CameraSnapshotRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraSnapshotResponse]:
    """Capture snapshot from camera."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access cameras",
        )

    result = await service.capture_snapshot(camera_id, request.timeout_seconds)

    if result.get("success"):
        return SuccessResponse(
            data=CameraSnapshotResponse(
                success=True,
                camera_id=camera_id,
                snapshot_id=result.get("snapshot_id"),
                storage_path=result.get("storage_path"),
                url=f"http://localhost:8000/snapshots/{result.get('snapshot_id')}",
            )
        )
    else:
        return SuccessResponse(
            data=CameraSnapshotResponse(
                success=False,
                camera_id=camera_id,
                error=result.get("error"),
            )
        )


@router.get("/summary", response_model=SuccessResponse[CameraSummaryResponse])
async def get_camera_summary(
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraSummaryResponse]:
    """Get camera system summary."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view cameras",
        )

    summary = await service.get_summary()
    from datetime import datetime

    return SuccessResponse(
        data=CameraSummaryResponse(
            total_cameras=summary.get("total_cameras", 0),
            active_cameras=summary.get("active_cameras", 0),
            offline_cameras=summary.get("offline_cameras", 0),
            recording_cameras=summary.get("recording_cameras", 0),
            detection_enabled=summary.get("detection_enabled", 0),
            total_groups=0,  # TODO: Implement group counting
            last_update=datetime.utcnow(),
            health_check_status=summary.get("health_check_status", "healthy"),
        )
    )


@router.post("/import", response_model=SuccessResponse[CameraImportResponse])
async def import_cameras(
    request: CameraImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
) -> SuccessResponse[CameraImportResponse]:
    """Import cameras from CSV or JSON."""
    if not current_user.has_permission("cameras:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage cameras",
        )

    try:
        # Decode base64 data
        file_data = base64.b64decode(request.data)

        # Parse based on format
        if request.format == "json":
            cameras_data = json.loads(file_data.decode())
            if isinstance(cameras_data, dict):
                cameras_data = cameras_data.get("cameras", [])
        else:  # CSV
            import csv
            import io

            file_content = file_data.decode()
            reader = csv.DictReader(io.StringIO(file_content))
            cameras_data = list(reader)

        # Import cameras
        result = await service.import_cameras(cameras_data, request.group_id)

        return SuccessResponse(
            data=CameraImportResponse(
                success=True,
                imported_count=result.get("imported_count", 0),
                skipped_count=result.get("skipped_count", 0),
                errors=result.get("errors", []),
            )
        )
    except Exception as e:
        return SuccessResponse(
            data=CameraImportResponse(
                success=False,
                imported_count=0,
                skipped_count=0,
                errors=[{"error": str(e)}],
            )
        )


@router.get("/export", response_model=SuccessResponse[CameraExportResponse])
async def export_cameras(
    current_user: CurrentUser = Depends(get_current_user),
    service: CameraService = Depends(get_camera_service),
    format: str = Query("csv", description="Export format: csv or json"),
    include_credentials: bool = Query(False),
    group_id: Optional[str] = Query(None),
) -> SuccessResponse[CameraExportResponse]:
    """Export cameras to CSV or JSON."""
    if not current_user.has_permission("cameras:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export cameras",
        )

    try:
        cameras_data = await service.export_cameras(group_id, include_credentials)

        if format == "json":
            import json
            data_str = json.dumps({"cameras": cameras_data, "count": len(cameras_data)})
            filename = f"cameras_{group_id or 'all'}.json" if group_id else "cameras_all.json"
        else:  # CSV
            import csv
            import io

            output = io.StringIO()
            if cameras_data:
                writer = csv.DictWriter(output, fieldnames=cameras_data[0].keys())
                writer.writeheader()
                writer.writerows(cameras_data)
            data_str = output.getvalue()
            filename = f"cameras_{group_id or 'all'}.csv" if group_id else "cameras_all.csv"

        # Encode to base64
        encoded_data = base64.b64encode(data_str.encode()).decode()

        return SuccessResponse(
            data=CameraExportResponse(
                success=True,
                format=format,
                data=encoded_data,
                camera_count=len(cameras_data),
                filename=filename,
            )
        )
    except Exception as e:
        return SuccessResponse(
            data=CameraExportResponse(
                success=False,
                format=format,
                data="",
                camera_count=0,
                filename="",
            )
        )
