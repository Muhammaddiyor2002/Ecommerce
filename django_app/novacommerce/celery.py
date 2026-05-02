"""Celery application bootstrap for NovaCommerce Core."""

from __future__ import annotations

import os

from celery import Celery
from celery.signals import setup_logging  # noqa: F401  (hook below)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novacommerce.settings.dev")

app = Celery("novacommerce")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover
    print(f"Request: {self.request!r}")
