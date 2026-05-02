from __future__ import annotations

from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "kind",
        "value",
        "used_count",
        "max_uses",
        "is_active",
        "starts_at",
        "ends_at",
    )
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name")
    date_hierarchy = "created_at"
