from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Review(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
        help_text="optional: link review to a verified purchase",
    )
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "reviews_review"
        unique_together = (("product", "user"),)
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "status", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
