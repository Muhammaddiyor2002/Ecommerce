from __future__ import annotations

from django.contrib import admin

from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount", "currency", "created_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("order__number", "provider_reference", "provider_intent_id")
    readonly_fields = ("id", "created_at", "updated_at", "raw_request", "raw_response", "error")
    date_hierarchy = "created_at"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "amount", "reason", "created_at")
    search_fields = ("payment__provider_reference", "provider_reference")
