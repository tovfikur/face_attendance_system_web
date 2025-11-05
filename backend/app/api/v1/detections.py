"""Detection endpoints."""

import base64
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.detection import (
    DetectionEventLogResponse,
    DetectionEventsQuery,
    DetectionMetricsResponse,
    DetectionProviderConfigCreate,
    DetectionProviderConfigResponse,
    DetectionProviderConfigUpdate,
    DetectionResponse,
    DetectionStatisticsResponse,
    DetectionWebSocketMessage,
    LiveDetectionsQuery,
    LiveDetectionsResponse,
    SendFrameRequest,
    SendFrameResponse,
    TestDetectionProviderRequest,
    TestDetectionProviderResponse,
    WebSocketSubscription,
)
from app.services.detection_service import DetectionService
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["Detections"])
logger = logging.getLogger(__name__)


# Helper functions
async def get_detection_service(db: AsyncSession = Depends(get_db)) -> DetectionService:
    """Get detection service."""
    return DetectionService(db)


# ============================================================================
# Provider Configuration Endpoints
# ============================================================================


@router.get("/provider/config", response_model=SuccessResponse[DetectionProviderConfigResponse])
async def get_provider_config(
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[DetectionProviderConfigResponse]:
    """Get active detection provider configuration."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view detection settings",
        )

    try:
        config = await service.get_provider_config()
        return SuccessResponse(
            data=DetectionProviderConfigResponse(
                id=config.id,
                provider_name=config.provider_name,
                provider_type=config.provider_type,
                endpoint_url=config.endpoint_url,
                api_key=config.api_key,
                api_secret=config.api_secret,
                timeout_seconds=config.timeout_seconds,
                max_faces_per_frame=config.max_faces_per_frame,
                confidence_threshold=config.confidence_threshold,
                enable_person_detection=config.enable_person_detection,
                enable_face_detection=config.enable_face_detection,
                enable_face_encoding=config.enable_face_encoding,
                is_active=config.is_active,
                last_tested=config.last_tested,
                test_status=config.test_status,
                last_error=config.last_error,
                createdAt=config.created_at,
                updatedAt=config.updated_at,
            )
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/provider/config", response_model=SuccessResponse[DetectionProviderConfigResponse])
async def update_provider_config(
    request: DetectionProviderConfigUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[DetectionProviderConfigResponse]:
    """Update detection provider configuration."""
    if not current_user.has_permission("detections:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage detection settings",
        )

    try:
        config = await service.get_provider_config()
        updated_config = await service.update_provider_config(config.id, request)

        return SuccessResponse(
            data=DetectionProviderConfigResponse(
                id=updated_config.id,
                provider_name=updated_config.provider_name,
                provider_type=updated_config.provider_type,
                endpoint_url=updated_config.endpoint_url,
                api_key=updated_config.api_key,
                api_secret=updated_config.api_secret,
                timeout_seconds=updated_config.timeout_seconds,
                max_faces_per_frame=updated_config.max_faces_per_frame,
                confidence_threshold=updated_config.confidence_threshold,
                enable_person_detection=updated_config.enable_person_detection,
                enable_face_detection=updated_config.enable_face_detection,
                enable_face_encoding=updated_config.enable_face_encoding,
                is_active=updated_config.is_active,
                last_tested=updated_config.last_tested,
                test_status=updated_config.test_status,
                last_error=updated_config.last_error,
                createdAt=updated_config.created_at,
                updatedAt=updated_config.updated_at,
            )
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Provider Testing Endpoints
# ============================================================================


@router.post("/test-provider", response_model=SuccessResponse[TestDetectionProviderResponse])
async def test_provider(
    request: TestDetectionProviderRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[TestDetectionProviderResponse]:
    """Test detection provider connection."""
    if not current_user.has_permission("detections:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to test detection provider",
        )

    try:
        result = await service.test_provider_connection(
            config_id=request.provider_config_id,
            timeout_seconds=request.timeout_seconds,
        )
        return SuccessResponse(data=result)
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Detection Endpoints
# ============================================================================


@router.get("/live", response_model=SuccessResponse[LiveDetectionsResponse])
async def get_live_detections(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    detection_type: Optional[str] = Query(None, description="Filter by detection type (person, face, vehicle)"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(100, ge=1, le=1000, description="Result limit"),
    offset: int = Query(0, ge=0, description="Result offset"),
    use_cache: bool = Query(True, description="Use Redis cache if available"),
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[LiveDetectionsResponse]:
    """Get live detections with optional caching."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view detections",
        )

    try:
        result = await service.get_live_detections(
            camera_id=camera_id,
            detection_type=detection_type,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset,
            use_cache=use_cache,
        )

        return SuccessResponse(
            data=LiveDetectionsResponse(
                camera_id=camera_id or "all",
                detections=[
                    DetectionResponse(
                        id=d.id,
                        camera_id=d.camera_id,
                        detection_type=d.detection_type,
                        confidence=d.confidence,
                        bbox={
                            "x": d.bbox_x,
                            "y": d.bbox_y,
                            "width": d.bbox_width,
                            "height": d.bbox_height,
                        },
                        person_name=d.person_name,
                        person_id=d.person_id,
                        face_encoding=d.face_encoding,
                        is_processed=d.is_processed,
                        processing_status=d.processing_status,
                        frame_number=d.frame_number,
                        frame_timestamp=d.frame_timestamp,
                        createdAt=d.created_at,
                        updatedAt=d.updated_at,
                    )
                    for d in result["detections"]
                ],
                total_detections=result["total_detections"],
                last_updated=result["last_updated"],
                cache_hit=result["cache_hit"],
            )
        )
    except Exception as e:
        logger.error(f"Error getting live detections: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get detections")


@router.post("/send-frame", response_model=SuccessResponse[SendFrameResponse], status_code=status.HTTP_201_CREATED)
async def send_frame_for_detection(
    request: SendFrameRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[SendFrameResponse]:
    """Send frame for detection processing."""
    if not current_user.has_permission("detections:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to send frames for detection",
        )

    try:
        # Decode base64 frame
        frame_data = base64.b64decode(request.frame_data)

        result = await service.send_frame_for_detection(
            camera_id=request.camera_id,
            frame_data=frame_data,
            frame_number=request.frame_number,
            frame_timestamp=request.timestamp,
        )

        return SuccessResponse(
            data=SendFrameResponse(
                success=result["success"],
                camera_id=result["camera_id"],
                detection_count=result["detection_count"],
                detections=[
                    DetectionResponse(
                        id=d.id,
                        camera_id=d.camera_id,
                        detection_type=d.detection_type,
                        confidence=d.confidence,
                        bbox={
                            "x": d.bbox_x,
                            "y": d.bbox_y,
                            "width": d.bbox_width,
                            "height": d.bbox_height,
                        },
                        person_name=d.person_name,
                        person_id=d.person_id,
                        face_encoding=d.face_encoding,
                        is_processed=d.is_processed,
                        processing_status=d.processing_status,
                        frame_number=d.frame_number,
                        frame_timestamp=d.frame_timestamp,
                        createdAt=d.created_at,
                        updatedAt=d.updated_at,
                    )
                    for d in result["detections"]
                ],
                processing_time_ms=result["processing_time_ms"],
            ),
            meta={"processing_time_ms": result["processing_time_ms"]},
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, Exception) as e:
        logger.error(f"Error sending frame for detection: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Detection Events Endpoints
# ============================================================================


@router.get("/events", response_model=PaginatedResponse[DetectionEventLogResponse])
async def get_detection_events(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    person_id: Optional[str] = Query(None, description="Filter by person ID"),
    limit: int = Query(100, ge=1, le=1000, description="Result limit"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> PaginatedResponse[DetectionEventLogResponse]:
    """Get detection events with filtering."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view detection events",
        )

    try:
        result = await service.get_detection_events(
            camera_id=camera_id,
            event_type=event_type,
            severity=severity,
            person_id=person_id,
            limit=limit,
            offset=offset,
        )

        events = result["events"]
        total = result["total_events"]
        page = offset // limit + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return PaginatedResponse(
            data=[
                DetectionEventLogResponse(
                    id=e.id,
                    detection_id=e.detection_id,
                    camera_id=e.camera_id,
                    event_type=e.event_type,
                    severity=e.severity,
                    message=e.message,
                    person_id=e.person_id,
                    person_name=e.person_name,
                    confidence_score=e.confidence_score,
                    action_taken=e.action_taken,
                    action_timestamp=e.action_timestamp,
                    source_system=e.source_system,
                    createdAt=e.created_at,
                    updatedAt=e.updated_at,
                )
                for e in events
            ],
            meta=PaginationMeta(
                page=page,
                pageSize=limit,
                total=total,
                totalPages=total_pages,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting detection events: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get events")


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/statistics", response_model=SuccessResponse[DetectionStatisticsResponse])
async def get_detection_statistics(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[DetectionStatisticsResponse]:
    """Get detection statistics."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view detection statistics",
        )

    try:
        stats = await service.get_detection_statistics(camera_id=camera_id)

        return SuccessResponse(
            data=DetectionStatisticsResponse(
                total_detections=stats["total_detections"],
                detections_today=stats["detections_today"],
                detections_this_hour=stats["detections_this_hour"],
                average_confidence=stats["average_confidence"],
                most_detected_person=stats["most_detected_person"],
                detection_types=stats["detection_types"],
                cameras_active=stats["cameras_active"],
                last_detection_timestamp=stats["last_detection_timestamp"],
            )
        )
    except Exception as e:
        logger.error(f"Error getting detection statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get statistics")


@router.get("/queue-stats", response_model=SuccessResponse[dict])
async def get_queue_stats(
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[dict]:
    """Get detection processing queue statistics."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view queue statistics",
        )

    try:
        stats = await service.get_queue_stats()
        return SuccessResponse(data=stats)
    except Exception as e:
        logger.error(f"Error getting queue statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get queue stats")


@router.get("/summary", response_model=SuccessResponse[dict])
async def get_detection_summary(
    current_user: CurrentUser = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> SuccessResponse[dict]:
    """Get detection system summary."""
    if not current_user.has_permission("detections:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view detection summary",
        )

    try:
        summary = await service.get_detection_summary()
        return SuccessResponse(data=summary)
    except Exception as e:
        logger.error(f"Error getting detection summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get summary")


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time detection streaming."""
    await ws_manager.connect(websocket, client_id)
    service = DetectionService(db)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                    }
                )
                continue

            # Handle subscription messages
            message_type = message.get("type", "").lower()

            if message_type == "subscribe":
                # Subscribe to a camera or event type
                camera_id = message.get("camera_id")
                event_types = message.get("event_types", [])
                min_confidence = message.get("min_confidence")

                if camera_id:
                    channel = f"camera:{camera_id}"
                    await ws_manager.subscribe(websocket, channel)

                    # Send current detections
                    result = await service.get_live_detections(
                        camera_id=camera_id,
                        min_confidence=min_confidence or 0.5,
                        use_cache=True,
                    )

                    detections_data = []
                    for d in result["detections"]:
                        detections_data.append(
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
                        )

                    await websocket.send_json(
                        {
                            "type": "subscription",
                            "camera_id": camera_id,
                            "subscribed": True,
                            "message": f"Subscribed to camera {camera_id}",
                            "current_detections": detections_data,
                            "detection_count": len(detections_data),
                        }
                    )

                if event_types:
                    for event_type in event_types:
                        channel = f"events:{event_type}"
                        await ws_manager.subscribe(websocket, channel)

                    await websocket.send_json(
                        {
                            "type": "subscription",
                            "event_types": event_types,
                            "subscribed": True,
                            "message": f"Subscribed to event types: {', '.join(event_types)}",
                        }
                    )

            elif message_type == "unsubscribe":
                # Unsubscribe from a camera or event type
                camera_id = message.get("camera_id")
                event_types = message.get("event_types", [])

                if camera_id:
                    channel = f"camera:{camera_id}"
                    await ws_manager.unsubscribe(websocket, channel)

                    await websocket.send_json(
                        {
                            "type": "subscription",
                            "camera_id": camera_id,
                            "subscribed": False,
                            "message": f"Unsubscribed from camera {camera_id}",
                        }
                    )

                if event_types:
                    for event_type in event_types:
                        channel = f"events:{event_type}"
                        await ws_manager.unsubscribe(websocket, channel)

                    await websocket.send_json(
                        {
                            "type": "subscription",
                            "event_types": event_types,
                            "subscribed": False,
                            "message": f"Unsubscribed from event types: {', '.join(event_types)}",
                        }
                    )

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                    }
                )

            elif message_type == "get_stats":
                # Get queue statistics
                stats = await service.get_queue_stats()
                await websocket.send_json(
                    {
                        "type": "stats",
                        "queue_stats": stats,
                    }
                )

            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    }
                )

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await ws_manager.disconnect(websocket, client_id)


async def broadcast_detection(
    detection_id: str,
    camera_id: str,
    detection_type: str,
    confidence: float,
    person_name: Optional[str] = None,
    person_id: Optional[str] = None,
):
    """Broadcast detection to subscribed clients."""
    channel = f"camera:{camera_id}"
    message = {
        "type": "detection",
        "detection_id": detection_id,
        "camera_id": camera_id,
        "detection_type": detection_type,
        "confidence": confidence,
        "person_name": person_name,
        "person_id": person_id,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
    await ws_manager.broadcast_to_channel(channel, message)


async def broadcast_event(
    event_id: str,
    event_type: str,
    severity: str,
    message_text: str,
    camera_id: Optional[str] = None,
):
    """Broadcast event to subscribed clients."""
    channel = f"events:{event_type}"
    message = {
        "type": "event",
        "event_id": event_id,
        "event_type": event_type,
        "severity": severity,
        "message": message_text,
        "camera_id": camera_id,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
    await ws_manager.broadcast_to_channel(channel, message)
