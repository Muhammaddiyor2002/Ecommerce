from __future__ import annotations

from django.contrib import admin

from .models import Order, OrderEvent, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "sku", "name_snapshot", "quantity", "unit_price", "line_total")


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ("code", "message", "actor", "payload", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "user",
        "status",
        "grand_total",
        "currency",
        "payment_provider",
        "created_at",
    )
    list_filter = ("status", "currency", "payment_provider")
    search_fields = ("number", "user__email", "email_snapshot", "payment_reference")
    date_hierarchy = "created_at"
    readonly_fields = (
        "id",
        "number",
        "subtotal",
        "shipping_total",
        "tax_total",
        "discount_total",
        "grand_total",
        "paid_at",
        "cancelled_at",
        "refunded_at",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline, OrderEventInline]


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ("order", "code", "actor", "created_at")
    list_filter = ("code",)
    search_fields = ("order__number", "code", "message")
