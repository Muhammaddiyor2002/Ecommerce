"""Shipment lifecycle (per order)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel


class ShippingMethod(TimeStampedUUIDModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    eta_days_min = models.PositiveIntegerField(default=1)
    eta_days_max = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)
    flat_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "shipping_method"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Shipment(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PREPARING = "preparing", _("Preparing")
        IN_TRANSIT = "in_transit", _("In transit")
        OUT_FOR_DELIVERY = "out_for_delivery", _("Out for delivery")
        DELIVERED = "delivered", _("Delivered")
        FAILED = "failed", _("Failed")
        RETURNED = "returned", _("Returned")

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="shipments")
    method = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT)
    courier = models.CharField(max_length=120, blank=True)
    tracking_number = models.CharField(max_length=64, blank=True, db_index=True)
    tracking_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PREPARING, db_index=True
    )
    eta = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "shipping_shipment"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "-created_at"])]
