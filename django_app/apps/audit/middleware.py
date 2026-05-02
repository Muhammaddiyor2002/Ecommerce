"""Audit middleware — records admin/api mutations made by staff users."""

from __future__ import annotations

import logging
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.middleware import get_request_id

logger = logging.getLogger(__name__)

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
SENSITIVE_PREFIXES = ("/admin/", "/api/admin/")


class AuditTrailMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.method not in MUTATING:
            return response
        if not any(request.path.startswith(p) for p in SENSITIVE_PREFIXES):
            return response
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response

        try:
            from .models import AuditLog

            AuditLog.objects.create(
                actor=request.user if request.user.is_authenticated else None,
                actor_email=getattr(request.user, "email", "") or "",
                action=f"{request.method} {request.path}",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                request_id=get_request_id(),
                payload={"status": response.status_code},
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("audit log write failed: %s", exc)
        return response
