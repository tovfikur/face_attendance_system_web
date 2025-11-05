"""Real-time attendance WebSocket endpoints for live attendance tracking."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Set
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocketDisconnect, status, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.person import PersonCurrentStatus
from app.services.attendance_service import AttendanceService

router = APIRouter(tags=["Attendance WebSocket"])
logger = logging.getLogger(__name__)


# In-memory connection manager for attendance updates
class AttendanceWebSocketManager:
    """Manages WebSocket connections for real-time attendance updates."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.person_subscriptions: dict[str, Set[str]] = {}  # person_id -> client_ids
        self.client_filters: dict[str, dict] = {}  # client_id -> filter settings

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        person_id: Optional[str] = None,
        min_confidence: float = 0.0,
    ):
        """Register a new WebSocket connection."""
        await websocket.accept()

        # Store connection
        if person_id not in self.active_connections:
            self.active_connections[person_id] = []
        self.active_connections[person_id].append(websocket)

        # Store subscription info
        if person_id not in self.person_subscriptions:
            self.person_subscriptions[person_id] = set()
        self.person_subscriptions[person_id].add(client_id)

        # Store filter settings
        self.client_filters[client_id] = {
            "person_id": person_id,
            "min_confidence": min_confidence,
        }

        logger.info(f"Client {client_id} connected for person {person_id or 'all'}")

    async def disconnect(self, client_id: str, person_id: Optional[str] = None):
        """Unregister a WebSocket connection."""
        if person_id and person_id in self.active_connections:
            # Remove from connections list
            self.active_connections[person_id] = [
                ws
                for ws in self.active_connections[person_id]
                if not (hasattr(ws, "_client_id") and ws._client_id == client_id)
            ]

            # Remove from subscriptions
            if person_id in self.person_subscriptions:
                self.person_subscriptions[person_id].discard(client_id)

                if not self.person_subscriptions[person_id]:
                    del self.person_subscriptions[person_id]

        # Remove filter settings
        self.client_filters.pop(client_id, None)
        logger.info(f"Client {client_id} disconnected")

    async def broadcast_attendance_event(
        self,
        event_type: str,
        person_id: str,
        person_name: str,
        action: str,
        timestamp: datetime,
        confidence: float,
        attendance_id: Optional[str] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
    ):
        """Broadcast attendance event to all subscribed clients."""
        event_data = {
            "type": event_type,
            "event_timestamp": datetime.utcnow().isoformat(),
            "person_id": person_id,
            "person_name": person_name,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "confidence": round(confidence, 3),
            "attendance_id": attendance_id,
        }

        if check_in_time:
            event_data["check_in_time"] = check_in_time.isoformat()

        if check_out_time:
            event_data["check_out_time"] = check_out_time.isoformat()

        if duration_minutes is not None:
            event_data["duration_minutes"] = duration_minutes

        message = json.dumps(event_data)

        # Broadcast to all connections for this person
        if person_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[person_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending attendance event: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected connections
            for ws in disconnected:
                self.active_connections[person_id].remove(ws)

        # Broadcast to "all persons" subscribers
        if "all" in self.active_connections:
            disconnected = []
            for websocket in self.active_connections["all"]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending attendance event: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected connections
            for ws in disconnected:
                self.active_connections["all"].remove(ws)

        logger.info(f"Broadcasted {event_type} for person {person_id} to subscribers")

    async def broadcast_status_update(
        self,
        person_id: str,
        person_name: str,
        checked_in: bool,
        check_in_time: Optional[datetime] = None,
        current_duration_minutes: Optional[int] = None,
    ):
        """Broadcast person status update."""
        event_data = {
            "type": "person_status_update",
            "event_timestamp": datetime.utcnow().isoformat(),
            "person_id": person_id,
            "person_name": person_name,
            "checked_in": checked_in,
            "check_in_time": check_in_time.isoformat() if check_in_time else None,
            "current_duration_minutes": current_duration_minutes,
        }

        message = json.dumps(event_data)

        # Broadcast to all connections for this person
        if person_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[person_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending status update: {e}")
                    disconnected.append(websocket)

            for ws in disconnected:
                self.active_connections[person_id].remove(ws)

        # Broadcast to "all persons" subscribers
        if "all" in self.active_connections:
            disconnected = []
            for websocket in self.active_connections["all"]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending status update: {e}")
                    disconnected.append(websocket)

            for ws in disconnected:
                self.active_connections["all"].remove(ws)

    async def send_ping(self, websocket: WebSocket):
        """Send keep-alive ping."""
        try:
            await websocket.send_json(
                {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error sending ping: {e}")


# Global connection manager
attendance_manager = AttendanceWebSocketManager()


# ============================================================================
# Real-time Attendance WebSocket Endpoint
# ============================================================================


@router.websocket("/ws/{client_id}")
async def websocket_attendance(
    websocket: WebSocket,
    client_id: str,
    person_id: Optional[str] = Query(None, description="Subscribe to specific person (None = all persons)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time attendance updates.

    Subscribe to attendance changes and receive live updates for check-ins/check-outs.

    Query Parameters:
    - person_id: Subscribe to specific person. If not specified, receives updates for all persons
    - min_confidence: Only receive events with confidence >= this threshold (0.0-1.0)

    Message Format (from server):
    - Type: "attendance_event" for check-in/check-out
    - Type: "person_status_update" for status changes
    - Type: "ping" for keep-alive
    - Type: "error" for error messages

    Example message:
    {
        "type": "attendance_event",
        "event_timestamp": "2024-01-15T10:30:45.123456",
        "person_id": "person_123",
        "person_name": "John Doe",
        "action": "check_in",
        "timestamp": "2024-01-15T10:30:45.123456",
        "confidence": 0.95,
        "attendance_id": "attendance_abc123",
        "check_in_time": "2024-01-15T10:30:45.123456",
        "duration_minutes": null
    }
    """
    client_id = client_id or str(uuid4())
    subscription_target = person_id or "all"

    try:
        # Connect the websocket
        await attendance_manager.connect(
            websocket,
            client_id,
            subscription_target,
            min_confidence,
        )

        # Store client_id on websocket for later reference
        websocket._client_id = client_id

        # Send welcome message
        await websocket.send_json(
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
                "subscribed_to": subscription_target,
                "min_confidence": min_confidence,
            }
        )

        # Send current status if person-specific subscription
        if person_id:
            service = AttendanceService(db)
            try:
                status_data = await service.get_current_check_in_status(person_id)
                await websocket.send_json(
                    {
                        "type": "initial_status",
                        "person_id": person_id,
                        "checked_in": status_data.get("checked_in", False),
                        "check_in_time": status_data.get("check_in_time", "").isoformat()
                        if status_data.get("check_in_time")
                        else None,
                        "current_duration_minutes": status_data.get("current_duration_minutes"),
                    }
                )
            except Exception as e:
                logger.warning(f"Error fetching initial status: {e}")

        # Keep-alive ping task
        async def send_pings():
            while True:
                try:
                    await asyncio.sleep(30)  # Send ping every 30 seconds
                    await attendance_manager.send_ping(websocket)
                except Exception as e:
                    logger.debug(f"Ping task error: {e}")
                    break

        ping_task = asyncio.create_task(send_pings())

        # Listen for messages from client
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client messages
                if message.get("type") == "pong":
                    logger.debug(f"Received pong from client {client_id}")
                elif message.get("type") == "subscribe":
                    # Client can subscribe to different person
                    new_person_id = message.get("person_id")
                    new_min_confidence = message.get("min_confidence", 0.0)

                    # Update subscription
                    if subscription_target != new_person_id:
                        await attendance_manager.disconnect(client_id, subscription_target)
                        await attendance_manager.connect(
                            websocket,
                            client_id,
                            new_person_id or "all",
                            new_min_confidence,
                        )

                        await websocket.send_json(
                            {
                                "type": "subscription_updated",
                                "new_subscription": new_person_id or "all",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                elif message.get("type") == "unsubscribe":
                    await websocket.send_json(
                        {
                            "type": "disconnecting",
                            "reason": "Client requested disconnect",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    break

        finally:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        await attendance_manager.disconnect(client_id, subscription_target)
        logger.info(f"WebSocket connection closed for client {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await attendance_manager.disconnect(client_id, subscription_target)


# ============================================================================
# Helper Functions for Broadcasting (to be called from services)
# ============================================================================


async def broadcast_check_in_event(
    person_id: str,
    person_name: str,
    timestamp: datetime,
    confidence: float,
    attendance_id: Optional[str] = None,
    check_in_time: Optional[datetime] = None,
):
    """Broadcast check-in event to all subscribed clients."""
    await attendance_manager.broadcast_attendance_event(
        event_type="attendance_event",
        person_id=person_id,
        person_name=person_name,
        action="check_in",
        timestamp=timestamp,
        confidence=confidence,
        attendance_id=attendance_id,
        check_in_time=check_in_time,
    )


async def broadcast_check_out_event(
    person_id: str,
    person_name: str,
    timestamp: datetime,
    confidence: float,
    attendance_id: Optional[str] = None,
    check_out_time: Optional[datetime] = None,
    duration_minutes: Optional[int] = None,
):
    """Broadcast check-out event to all subscribed clients."""
    await attendance_manager.broadcast_attendance_event(
        event_type="attendance_event",
        person_id=person_id,
        person_name=person_name,
        action="check_out",
        timestamp=timestamp,
        confidence=confidence,
        attendance_id=attendance_id,
        check_out_time=check_out_time,
        duration_minutes=duration_minutes,
    )


async def broadcast_person_status(
    person_id: str,
    person_name: str,
    checked_in: bool,
    check_in_time: Optional[datetime] = None,
    current_duration_minutes: Optional[int] = None,
):
    """Broadcast person status update to all subscribed clients."""
    await attendance_manager.broadcast_status_update(
        person_id=person_id,
        person_name=person_name,
        checked_in=checked_in,
        check_in_time=check_in_time,
        current_duration_minutes=current_duration_minutes,
    )
