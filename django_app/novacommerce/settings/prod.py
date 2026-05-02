"""Production settings — strict security, no debug, structured logs."""

from __future__ import annotations

from .base import *
from .base import env

DEBUG = False

# HTTPS / cookies
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # CSRF token must be JS-readable for SPAs
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

# Storage (S3 if configured)
if env("S3_BUCKET", default=""):
    AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET")
    AWS_S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default=None)
    AWS_S3_REGION_NAME = env("S3_REGION", default="us-east-1")
    AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY", default="")
    AWS_SECRET_ACCESS_KEY = env("S3_SECRET_KEY", default="")
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
