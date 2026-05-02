from __future__ import annotations

from django.contrib import admin

from .models import DailySalesSnapshot


@admin.register(DailySalesSnapshot)
class DailySalesSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "day",
        "orders_count",
        "paid_orders_count",
        "revenue",
        "average_order_value",
        "items_sold",
    )
    date_hierarchy = "day"
