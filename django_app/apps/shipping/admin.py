from __future__ import annotations

from django.contrib import admin

from .models import Shipment, ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "flat_rate", "is_active", "eta_days_min", "eta_days_max")
    list_filter = ("is_active",)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("order", "courier", "tracking_number", "status", "eta", "delivered_at")
    list_filter = ("status", "courier")
    search_fields = ("order__number", "tracking_number", "courier")
