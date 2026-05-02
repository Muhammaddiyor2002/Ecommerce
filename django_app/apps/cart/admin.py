from __future__ import annotations

from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("unit_price", "line_total")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "currency", "last_active_at")
    list_filter = ("currency",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]
