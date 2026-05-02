"""WebSocket consumers (Django Channels).

Three primary streams:
    /ws/orders/<order_id>/       — order lifecycle updates for a specific order
    /ws/me/                      — authenticated user firehose (orders, notifications)
    /ws/admin/dashboard/         — staff dashboard live metrics
"""

from __future__ import annotations

import logging
from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class OrderStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order.{self.order_id}"
        user = self.scope.get("user")

        # Authorization: order owner or staff. Anonymous denied.
        from django.contrib.auth.models import AnonymousUser

        if isinstance(user, AnonymousUser) or not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        owns = await self._user_owns_order(user.id, self.order_id, user.is_staff)
        if not owns:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "order_id": self.order_id})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_event(self, event: dict[str, Any]):
        await self.send_json(event)

    @staticmethod
    async def _user_owns_order(user_id, order_id, is_staff: bool) -> bool:
        from channels.db import database_sync_to_async

        from apps.orders.models import Order

        if is_staff:
            return True

        @database_sync_to_async
        def _check():
            return Order.objects.filter(pk=order_id, user_id=user_id).exists()

        return await _check()


class UserFirehoseConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return
        self.group_name = f"user.{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected"})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_event(self, event):
        await self.send_json(event)

    async def notification(self, event):
        await self.send_json(event)


class AdminDashboardConsumer(AsyncJsonWebsocketConsumer):
    GROUP = "admin.dashboard"

    async def connect(self):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_staff", False):
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "channel": self.GROUP})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def metric(self, event):
        await self.send_json(event)

    async def order_event(self, event):
        await self.send_json(event)
