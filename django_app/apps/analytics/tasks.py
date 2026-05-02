"""Daily analytics rollup tasks."""

from __future__ import annotations

import datetime as _dt
import logging
from decimal import Decimal

from celery import shared_task
from django.db.models import Avg, Sum
from django.utils import timezone

from apps.orders.models import Order

from .models import DailySalesSnapshot

logger = logging.getLogger(__name__)


@shared_task
def rollup_daily_sales(day: str | None = None) -> dict:
    target = _dt.date.fromisoformat(day) if day else (timezone.now().date() - _dt.timedelta(days=1))
    qs = Order.objects.filter(created_at__date=target)
    paid = qs.filter(status=Order.Status.PAID)
    revenue = paid.aggregate(s=Sum("grand_total"))["s"] or Decimal("0.00")
    aov = paid.aggregate(a=Avg("grand_total"))["a"] or Decimal("0.00")

    snap, _ = DailySalesSnapshot.objects.update_or_create(
        day=target,
        defaults={
            "orders_count": qs.count(),
            "paid_orders_count": paid.count(),
            "cancelled_orders_count": qs.filter(status=Order.Status.CANCELLED).count(),
            "revenue": revenue,
            "average_order_value": aov,
        },
    )
    logger.info("rolled up %s: revenue=%s", target, revenue)
    return {"day": target.isoformat(), "revenue": str(revenue)}
