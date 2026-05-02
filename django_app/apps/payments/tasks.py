"""Celery tasks for payment housekeeping."""

from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from .models import Payment

logger = logging.getLogger(__name__)


@shared_task
def expire_pending_payments(older_than_minutes: int = 60) -> int:
    """Mark stale pending payments as failed; called by Celery beat."""
    cutoff = timezone.now() - timezone.timedelta(minutes=older_than_minutes)
    qs = Payment.objects.filter(status=Payment.Status.PENDING, created_at__lt=cutoff)
    n = qs.update(status=Payment.Status.FAILED, error={"reason": "expired"})
    if n:
        logger.info("expired %s pending payments", n)
    return n
