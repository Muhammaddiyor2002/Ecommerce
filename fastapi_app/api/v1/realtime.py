"""Public WebSocket endpoints (flash sale counters, live stock counters).

These are the *public* WS endpoints; authenticated user-specific streams
(order tracking, dashboard) live in the Django Channels service.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...realtime.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/flash-sale/{sale_id}")
async def flash_sale_ws(websocket: WebSocket, sale_id: str):
    """Counter for items remaining + countdown."""
    channel = f"flash_sale.{sale_id}"
    await manager.connect(websocket, channel)
    try:
        while True:
            # Echo client pings for keep-alive; real updates come via pub/sub.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, channel)


@router.websocket("/ws/stock/{sku}")
async def stock_ws(websocket: WebSocket, sku: str):
    """Live stock count for a SKU. Useful for product detail pages."""
    channel = f"stock.{sku}"
    await manager.connect(websocket, channel)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, channel)
