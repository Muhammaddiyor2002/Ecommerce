"""Development settings — verbose, permissive, with debug toolbar."""

from __future__ import annotations

from .base import *
from .base import INSTALLED_APPS, MIDDLEWARE, env  # explicit refs for type-checkers

DEBUG = True

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar", "django_extensions"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

CORS_ALLOW_ALL_ORIGINS = True

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
