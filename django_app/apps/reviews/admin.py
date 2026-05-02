from __future__ import annotations

from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    search_fields = ("product__name", "user__email", "title")
    actions = ["approve", "reject"]

    @admin.action(description="Approve selected")
    def approve(self, request, queryset):
        queryset.update(status=Review.Status.APPROVED)

    @admin.action(description="Reject selected")
    def reject(self, request, queryset):
        queryset.update(status=Review.Status.REJECTED)
