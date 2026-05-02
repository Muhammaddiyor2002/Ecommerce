"""Cart models — supports anonymous (session_key) and authenticated carts."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Cart(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    session_key = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="For anonymous carts. Cleared when merged into a user cart.",
    )
    currency = models.CharField(max_length=3, default="USD")
    coupon = models.ForeignKey(
        "coupons.Coupon", null=True, blank=True, on_delete=models.SET_NULL, related_name="carts"
    )
    metadata = models.JSONField(default=dict, blank=True)
    last_active_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        owner = self.user.email if self.user_id else f"anon:{self.session_key[:8]}"
        return f"Cart<{owner}>"

    def subtotal(self) -> Decimal:
        return sum((it.line_total for it in self.items.all()), start=Decimal("0.00"))

    def total_items(self) -> int:
        return sum(it.quantity for it in self.items.all())


class CartItem(TimeStampedUUIDModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "cart_item"
        unique_together = (("cart", "variant"),)
        indexes = [models.Index(fields=["cart"])]

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))
