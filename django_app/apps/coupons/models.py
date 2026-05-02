"""Coupons / promotion codes."""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel


class Coupon(TimeStampedUUIDModel):
    class Kind(models.TextChoices):
        PERCENT = "percent", _("Percent off")
        FIXED = "fixed", _("Fixed amount off")
        FREE_SHIPPING = "free_shipping", _("Free shipping")

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.PERCENT)
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Percent (0-100) or fixed currency amount."),
    )
    min_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    max_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Cap for percentage discounts."),
    )
    max_uses = models.PositiveIntegerField(default=0, help_text=_("0 = unlimited"))
    used_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "coupons_coupon"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def is_valid_now(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        if subtotal < self.min_subtotal:
            return Decimal("0.00")
        if self.kind == self.Kind.PERCENT:
            disc = (subtotal * self.value / Decimal("100")).quantize(Decimal("0.01"))
            if self.max_discount:
                disc = min(disc, self.max_discount)
            return disc
        if self.kind == self.Kind.FIXED:
            return min(self.value, subtotal)
        return Decimal("0.00")
