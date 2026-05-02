"""Admin/internal API surface (Django).

Catalog mutation, inventory, coupons, orders, reports, etc. Read-heavy
public endpoints live in the FastAPI service.
"""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("catalog/", include("apps.catalog.admin_urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("coupons/", include("apps.coupons.urls")),
    path("analytics/", include("apps.analytics.urls")),
]
