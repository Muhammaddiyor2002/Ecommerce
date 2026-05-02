from __future__ import annotations

from django.apps import AppConfig


class CheckoutConfig(AppConfig):
    name = "apps.checkout"
    label = "checkout"
    verbose_name = "Checkout"
    default_auto_field = "django.db.models.BigAutoField"
