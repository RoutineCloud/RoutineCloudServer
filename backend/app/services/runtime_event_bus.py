from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.schemas.runtime import RuntimeEventEnvelope


class RuntimeEventBus:
    def __init__(self) -> None:
        self._queues: dict[int, set[asyncio.Queue[RuntimeEventEnvelope]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def subscribe(self, user_id: int) -> AsyncIterator[asyncio.Queue[RuntimeEventEnvelope]]:
        queue: asyncio.Queue[RuntimeEventEnvelope] = asyncio.Queue()
        async with self._lock:
            self._queues[user_id].add(queue)
        try:
            yield queue
        finally:
            async with self._lock:
                queues = self._queues.get(user_id)
                if queues is None:
                    return
                queues.discard(queue)
                if not queues:
                    self._queues.pop(user_id, None)

    async def publish(self, user_id: int, event: RuntimeEventEnvelope) -> None:
        async with self._lock:
            queues = list(self._queues.get(user_id, set()))
        for queue in queues:
            await queue.put(event)


runtime_event_bus = RuntimeEventBus()
