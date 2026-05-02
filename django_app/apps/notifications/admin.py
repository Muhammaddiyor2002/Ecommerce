from __future__ import annotations

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "channel", "template_code", "status", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("user__email", "template_code", "title")
    readonly_fields = ("id", "created_at", "updated_at", "sent_at", "read_at")
