from __future__ import annotations

from typing import Any, Optional

from pydantic_socketio import AsyncServer


class SocketIOBus:
    def __init__(self) -> None:
        self._sio: Optional[AsyncServer] = None
        self._namespace: Optional[str] = None

    def configure(self, sio: AsyncServer, namespace: str) -> None:
        self._sio = sio
        self._namespace = namespace

    async def emit_to_user(self, user_id: int, event: str, payload: Any) -> None:
        if not self._sio or not self._namespace:
            return
        await self._sio.emit(event, payload, room=f"user:{user_id}", namespace=self._namespace)


socketio_bus = SocketIOBus()
