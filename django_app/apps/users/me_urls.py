from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AddressViewSet, MeView

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="me-addresses")

urlpatterns = [
    path("", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
