"""Test settings — fast in-memory caches, eager celery, sqlite fallback."""

from __future__ import annotations

import os

# Provide minimal env defaults so base.py can import without a real .env.
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_db.sqlite3")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_CACHE_URL", "redis://localhost:6379/1")
os.environ.setdefault("REDIS_CHANNELS_URL", "redis://localhost:6379/2")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

from .base import *

DEBUG = False
TESTING = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# SQLite doesn't accept `connect_timeout` — strip postgres-specific options.
for _alias, _cfg in DATABASES.items():
    _cfg.pop("OPTIONS", None)
    _cfg["CONN_MAX_AGE"] = 0
    _cfg["CONN_HEALTH_CHECKS"] = False
    _cfg["ATOMIC_REQUESTS"] = False

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Speed up password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
