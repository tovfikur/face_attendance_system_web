"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Callable, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcasting."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket client connected: {client_id}")

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Unregister and close a WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe connection to a channel."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
            logger.debug(f"Client subscribed to channel: {channel}")

    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe connection from a channel."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
            logger.debug(f"Client unsubscribed from channel: {channel}")

    async def broadcast_to_channel(
        self,
        channel: str,
        message: dict,
        exclude_connection: Optional[WebSocket] = None,
    ):
        """Broadcast message to all connections subscribed to a channel."""
        disconnected = []

        for websocket, channels in self.subscriptions.items():
            if channel in channels and websocket != exclude_connection:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            # Find and remove from active connections
            for client_id, conns in list(self.active_connections.items()):
                if websocket in conns:
                    await self.disconnect(websocket, client_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []

        for client_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.append((client_id, websocket))

        # Clean up disconnected connections
        for client_id, websocket in disconnected:
            await self.disconnect(websocket, client_id)

    def get_subscriptions(self, websocket: WebSocket) -> set[str]:
        """Get channels subscribed by a connection."""
        return self.subscriptions.get(websocket, set())

    def get_channel_subscribers(self, channel: str) -> int:
        """Get number of subscribers to a channel."""
        count = 0
        for channels in self.subscriptions.values():
            if channel in channels:
                count += 1
        return count

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
ws_manager = ConnectionManager()
