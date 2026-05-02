"""Channels routing for WebSocket endpoints."""

from __future__ import annotations

from django.urls import re_path

from .consumers import (
    AdminDashboardConsumer,
    OrderStatusConsumer,
    UserFirehoseConsumer,
)

websocket_urlpatterns = [
    re_path(r"^ws/orders/(?P<order_id>[0-9a-f-]+)/$", OrderStatusConsumer.as_asgi()),
    re_path(r"^ws/me/$", UserFirehoseConsumer.as_asgi()),
    re_path(r"^ws/admin/dashboard/$", AdminDashboardConsumer.as_asgi()),
]
