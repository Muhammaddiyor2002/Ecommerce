r"""Order lifecycle.

Status state machine::

    PENDING  -> PAID -> PACKED -> SHIPPED -> DELIVERED
                  \                  \
                   v                   v
                CANCELLED            REFUNDED

Pricing:
    subtotal + shipping + tax - discount = total
All money fields are stored as Decimal in the order's currency at order time.
A snapshot of buyer + items is taken so changes to source records don't
mutate historical orders.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel
from apps.core.utils import generate_order_number


class Order(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PAID = "paid", _("Paid")
        PACKED = "packed", _("Packed")
        SHIPPED = "shipped", _("Shipped")
        DELIVERED = "delivered", _("Delivered")
        CANCELLED = "cancelled", _("Cancelled")
        REFUNDED = "refunded", _("Refunded")

    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.PAID, Status.CANCELLED},
        Status.PAID: {Status.PACKED, Status.CANCELLED, Status.REFUNDED},
        Status.PACKED: {Status.SHIPPED, Status.CANCELLED, Status.REFUNDED},
        Status.SHIPPED: {Status.DELIVERED, Status.REFUNDED},
        Status.DELIVERED: {Status.REFUNDED},
        Status.CANCELLED: set(),
        Status.REFUNDED: set(),
    }

    number = models.CharField(max_length=32, unique=True, default=generate_order_number)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    email_snapshot = models.EmailField(help_text=_("buyer email at the time of order"))
    phone_snapshot = models.CharField(max_length=24, blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    currency = models.CharField(max_length=3, default="USD")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    coupon_code = models.CharField(max_length=64, blank=True)

    shipping_address = models.JSONField(default=dict, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)

    payment_provider = models.CharField(max_length=32, blank=True)
    payment_reference = models.CharField(max_length=128, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    notes_internal = models.TextField(blank=True)
    notes_customer = models.TextField(blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "orders_order"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["payment_reference"]),
        ]

    def __str__(self) -> str:
        return self.number

    def can_transition_to(self, new: Order.Status) -> bool:
        return new in self.ALLOWED_TRANSITIONS.get(self.Status(self.status), set())


class OrderItem(TimeStampedUUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )
    sku = models.CharField(max_length=64)
    name_snapshot = models.CharField(max_length=255)
    attributes_snapshot = models.JSONField(default=dict, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "orders_item"
        indexes = [models.Index(fields=["order"])]

    def __str__(self) -> str:
        return f"{self.sku} x {self.quantity}"


class OrderEvent(TimeStampedUUIDModel):
    """Audit log of order lifecycle changes (status transitions, payment events)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    code = models.CharField(max_length=64)
    message = models.CharField(max_length=500, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "orders_event"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "-created_at"])]
