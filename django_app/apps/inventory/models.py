"""Inventory tracking with multi-warehouse support and stock reservations.

Concurrency notes:
- Stock writes use ``select_for_update()`` to prevent oversells.
- ``Stock.reserved`` holds units committed to active checkouts/carts.
- Available stock = on_hand - reserved - safety_buffer
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel


class Warehouse(TimeStampedUUIDModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(
        default=10,
        help_text=_("Lower number = higher priority for fulfilment."),
    )

    class Meta:
        db_table = "inventory_warehouse"
        ordering = ["priority", "name"]

    def __str__(self) -> str:
        return self.name


class Stock(TimeStampedUUIDModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="stocks"
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    safety_buffer = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        db_table = "inventory_stock"
        unique_together = (("variant", "warehouse"),)
        indexes = [
            models.Index(fields=["variant"]),
            models.Index(fields=["warehouse"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} @ {self.warehouse.code}: {self.on_hand}"

    @property
    def available(self) -> int:
        return max(self.on_hand - self.reserved - self.safety_buffer, 0)

    @property
    def is_low(self) -> bool:
        return self.available <= self.low_stock_threshold


class StockMovement(TimeStampedUUIDModel):
    """Audit trail of every stock change (adjustments, sales, refunds)."""

    class Reason(models.TextChoices):
        PURCHASE = "purchase", _("Purchase / restock")
        SALE = "sale", _("Sale")
        RETURN = "return", _("Return")
        ADJUSTMENT = "adjustment", _("Adjustment")
        TRANSFER_IN = "transfer_in", _("Transfer in")
        TRANSFER_OUT = "transfer_out", _("Transfer out")
        RESERVATION = "reservation", _("Reservation")
        RESERVATION_RELEASE = "reservation_release", _("Reservation release")

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="movements")
    quantity = models.IntegerField(help_text=_("Signed; negative for outflow."))
    reason = models.CharField(max_length=32, choices=Reason.choices)
    reference = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Optional FK reference (e.g. order_id)."),
    )
    note = models.TextField(blank=True)

    class Meta:
        db_table = "inventory_stock_movement"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["stock", "-created_at"]),
            models.Index(fields=["reason"]),
        ]
