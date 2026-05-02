"""Celery tasks for sending notifications via various channels."""

from __future__ import annotations

import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_email_notification(self, notification_id: str) -> None:
    n = Notification.objects.filter(pk=notification_id).first()
    if not n or n.status == Notification.Status.SENT:
        return
    to = (n.payload or {}).get("to") or (n.user.email if n.user_id else None)
    if not to:
        n.status = Notification.Status.FAILED
        n.save(update_fields=["status"])
        return
    try:
        send_mail(
            subject=n.title or "Notification",
            message=n.body,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[to],
            fail_silently=False,
        )
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
        n.save(update_fields=["status", "sent_at"])
    except Exception as exc:
        logger.warning("email send failed: %s", exc)
        n.status = Notification.Status.FAILED
        n.save(update_fields=["status"])
        raise self.retry(exc=exc)


@shared_task
def send_order_paid_email(order_id: str) -> None:
    """Hook called when an order transitions to PAID."""
    from apps.orders.models import Order

    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return
    n = Notification.objects.create(
        user=order.user,
        channel=Notification.Channel.EMAIL,
        template_code="order.paid",
        title=f"Order {order.number} paid",
        body=(
            f"Hi! Your order {order.number} totalling "
            f"{order.grand_total} {order.currency} has been received and paid. "
            "We'll notify you once it ships."
        ),
        payload={"to": order.email_snapshot, "order_id": str(order.id)},
    )
    send_email_notification.delay(str(n.id))
