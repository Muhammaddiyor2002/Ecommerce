from __future__ import annotations

from django.apps import AppConfig


class ShippingConfig(AppConfig):
    name = "apps.shipping"
    label = "shipping"
    verbose_name = "Shipping"
    default_auto_field = "django.db.models.BigAutoField"
