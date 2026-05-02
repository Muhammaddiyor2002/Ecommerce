"""NovaCommerce Core — Django project package."""

from __future__ import annotations

# Eager-load Celery so shared_task decorators work everywhere.
from .celery import app as celery_app

__all__ = ("celery_app",)
