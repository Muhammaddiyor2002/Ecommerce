"""Top-level URL routes for Django.

The Django service exposes:
    /admin/             — Django admin
    /api/admin/         — DRF API for admin/internal use
    /api/v1/auth/       — auth endpoints (login/register/refresh)
    /api/v1/me/         — authenticated user resources
    /api/v1/orders/     — order management (writes via Django for ACID safety)
    /api/v1/payments/   — payment webhooks & status
    /healthz            — liveness probe

High-volume read APIs (catalog, search) are served by the FastAPI service.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def healthz(_request):
    return JsonResponse({"status": "ok", "service": "django"})


urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),
    path("api/admin/", include("apps.core.api.admin_urls")),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/me/", include("apps.users.me_urls")),
    path("api/v1/", include("apps.cart.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/reviews/", include("apps.reviews.urls")),
    # OpenAPI / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:  # pragma: no cover
        pass
