from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
    class Channel(models.TextChoices):
        EMAIL = "email"
        SMS = "sms"
        PUSH = "push"
        TELEGRAM = "telegram"
        IN_APP = "in_app"

    class Status(models.TextChoices):
        PENDING = "pending"
        SENT = "sent"
        FAILED = "failed"
        READ = "read"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    channel = models.CharField(max_length=16, choices=Channel.choices)
    template_code = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["channel", "status"]),
        ]
