"""Pre-aggregated analytics tables, populated by Celery beat tasks."""

from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class DailySalesSnapshot(TimeStampedUUIDModel):
    day = models.DateField(unique=True, db_index=True)
    orders_count = models.PositiveIntegerField(default=0)
    paid_orders_count = models.PositiveIntegerField(default=0)
    cancelled_orders_count = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    items_sold = models.PositiveIntegerField(default=0)
    new_customers = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "analytics_daily_sales"
        ordering = ["-day"]
