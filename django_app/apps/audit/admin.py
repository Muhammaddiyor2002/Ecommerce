from __future__ import annotations

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "target_type", "target_id", "ip_address", "created_at")
    list_filter = ("action",)
    search_fields = ("actor_email", "action", "target_id", "request_id")
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
