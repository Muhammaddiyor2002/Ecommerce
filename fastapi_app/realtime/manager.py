"""WebSocket connection manager with Redis pub/sub backplane.

Each client subscribes to one or more channels (e.g. flash_sale.<id>,
stock.<sku>). When a message is published to the channel via Redis (typically
by Celery tasks or Django signals), it is fanned out to all websockets in
that channel.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from ..core.redis import get_pubsub

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._pubsub_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._channels[channel].add(websocket)
            if channel not in self._pubsub_tasks:
                task = asyncio.create_task(self._consume(channel))
                self._pubsub_tasks[channel] = task

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        async with self._lock:
            self._channels[channel].discard(websocket)
            if not self._channels[channel]:
                self._channels.pop(channel, None)
                task = self._pubsub_tasks.pop(channel, None)
                if task:
                    task.cancel()

    async def broadcast(self, channel: str, message: Any) -> None:
        # Local fanout helper for in-process tests.
        for ws in list(self._channels.get(channel, ())):
            try:
                await ws.send_json(message)
            except Exception:  # pragma: no cover
                self._channels[channel].discard(ws)

    async def _consume(self, channel: str) -> None:
        """Subscribe to a Redis pub/sub channel and fan out to websockets."""
        try:
            r = await get_pubsub()
            ps = r.pubsub()
            await ps.subscribe(channel)
            async for message in ps.listen():
                if message.get("type") != "message":
                    continue
                payload = message.get("data")
                # Send raw to each websocket
                for ws in list(self._channels.get(channel, ())):
                    try:
                        await ws.send_text(
                            payload if isinstance(payload, str) else payload.decode("utf-8")
                        )
                    except Exception:  # pragma: no cover
                        self._channels[channel].discard(ws)
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.exception("pubsub consumer crashed for %s: %s", channel, exc)


manager = ConnectionManager()
