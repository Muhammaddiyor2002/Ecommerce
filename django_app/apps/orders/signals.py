"""Order signal hooks — broadcast realtime status updates."""

from __future__ import annotations

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OrderEvent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderEvent)
def broadcast_order_event(sender, instance: OrderEvent, created: bool, **kwargs):
    if not created:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    payload = {
        "type": "order.event",
        "order_id": str(instance.order_id),
        "code": instance.code,
        "message": instance.message,
        "status": instance.order.status,
    }
    try:
        async_to_sync(layer.group_send)(f"order.{instance.order_id}", payload)
        if instance.order.user_id:
            async_to_sync(layer.group_send)(f"user.{instance.order.user_id}", payload)
    except Exception as exc:  # pragma: no cover
        logger.warning("could not broadcast order event: %s", exc)
