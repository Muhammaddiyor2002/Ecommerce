"""Cross-cutting middleware (request id, structured log binding)."""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

REQUEST_ID_HEADER = "X-Request-ID"
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def get_request_id() -> str:
    return _request_id_var.get()


class RequestIDMiddleware:
    """Attach a stable request id to each request, surfaced in logs and headers."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = _request_id_var.set(rid)
        try:
            request.request_id = rid  # type: ignore[attr-defined]
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = rid
            return response
        finally:
            _request_id_var.reset(token)
