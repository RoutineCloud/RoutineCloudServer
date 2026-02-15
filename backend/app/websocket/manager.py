from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Set, Any

from fastapi import WebSocket


class ConnectionManager:
    """
    Tracks active WebSocket connections per user.
    Provides utilities to send JSON messages to a user's connections.
    """

    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept a new WebSocke
        """
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(user_id)
            if not conns:
                return
            conns.discard(websocket)
            websocket.close()
            if not conns:
                self._connections.pop(user_id, None)


    async def broadcast_message(self, user_id: int, message: Dict[str, Any]) -> None:
        async with self._lock:
            conns = list(self._connections.get(user_id, set()))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(user_id, ws)

    async def push_routine_event(self, user_id: int, routine_id: int, action: str) -> None:
        # Broadcast a routine control event to all active connections for the user
        await self.broadcast_message(
            user_id,
            {
                "type": "command",
                "command": action,
                "data": {
                    "routine_id": routine_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            },
        )


# Singleton manager instance
ws_manager = ConnectionManager()
