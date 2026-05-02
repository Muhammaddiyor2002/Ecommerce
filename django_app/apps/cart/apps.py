from __future__ import annotations

from django.apps import AppConfig


class CartConfig(AppConfig):
    name = "apps.cart"
    label = "cart"
    verbose_name = "Cart"
    default_auto_field = "django.db.models.BigAutoField"
