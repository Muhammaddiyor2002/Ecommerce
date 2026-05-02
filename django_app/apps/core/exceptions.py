"""Unified API exception handler — predictable JSON error envelopes."""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """DRF exception handler that always returns the same shape:

    {"error": {"code": "...", "message": "...", "details": {...}}}
    """
    response = drf_default_handler(exc, context)

    if response is None:
        # Map non-DRF exceptions
        if isinstance(exc, Http404):
            return Response(
                {"error": {"code": "not_found", "message": "Resource not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if isinstance(exc, DjangoValidationError):
            return Response(
                {
                    "error": {
                        "code": "validation",
                        "message": "Validation failed.",
                        "details": exc.message_dict
                        if hasattr(exc, "message_dict")
                        else exc.messages,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(exc, PermissionDenied):
            return Response(
                {"error": {"code": "forbidden", "message": str(exc)}},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Unhandled — log + 500
        logger.exception("unhandled exception in API: %s", exc)
        return Response(
            {"error": {"code": "internal", "message": "Internal server error."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalise DRF errors
    if isinstance(exc, APIException):
        code = getattr(exc, "default_code", "error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        details = exc.detail if isinstance(exc.detail, dict | list) else None
        response.data = {"error": {"code": code, "message": message, "details": details}}
    return response
