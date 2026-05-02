from __future__ import annotations

from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = "apps.reviews"
    label = "reviews"
    verbose_name = "Reviews"
    default_auto_field = "django.db.models.BigAutoField"
