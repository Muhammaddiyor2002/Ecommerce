from __future__ import annotations

from django.apps import AppConfig


class CouponsConfig(AppConfig):
    name = "apps.coupons"
    label = "coupons"
    verbose_name = "Coupons"
    default_auto_field = "django.db.models.BigAutoField"
