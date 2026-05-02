from __future__ import annotations

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "apps.orders"
    label = "orders"
    verbose_name = "Orders"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:  # pragma: no cover
        from . import signals  # noqa: F401
