from __future__ import annotations

from django.contrib import admin

from .models import Stock, StockMovement, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "priority")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("variant", "warehouse", "on_hand", "reserved", "available", "is_low")
    list_filter = ("warehouse",)
    search_fields = ("variant__sku", "variant__product__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("stock", "quantity", "reason", "reference", "created_at")
    list_filter = ("reason",)
    search_fields = ("reference", "stock__variant__sku")
    date_hierarchy = "created_at"
