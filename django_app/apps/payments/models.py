"""Payment records.

Each ``Payment`` represents a charge attempt for an order. Webhooks update
status; refunds are children records.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel


class Payment(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        AUTHORIZED = "authorized", _("Authorized")
        CAPTURED = "captured", _("Captured")
        FAILED = "failed", _("Failed")
        CANCELLED = "cancelled", _("Cancelled")
        REFUNDED = "refunded", _("Refunded")

    class Provider(models.TextChoices):
        STRIPE = "stripe"
        PAYPAL = "paypal"
        CLICK = "click"
        PAYME = "payme"
        UZUM = "uzum"
        MANUAL = "manual"

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=24, choices=Provider.choices)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")

    provider_reference = models.CharField(max_length=128, blank=True, db_index=True)
    provider_intent_id = models.CharField(max_length=128, blank=True, db_index=True)
    redirect_url = models.URLField(blank=True)

    raw_request = models.JSONField(default=dict, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    error = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments_payment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
            models.Index(fields=["provider", "status"]),
        ]


class Refund(TimeStampedUUIDModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments_refund"
        ordering = ["-created_at"]
