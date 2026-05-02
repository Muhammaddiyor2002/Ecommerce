from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .admin_views import BrandViewSet, CategoryViewSet, ProductVariantViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"brands", BrandViewSet, basename="admin-brands")
router.register(r"categories", CategoryViewSet, basename="admin-categories")
router.register(r"products", ProductViewSet, basename="admin-products")
router.register(r"variants", ProductVariantViewSet, basename="admin-variants")

urlpatterns = [
    path("", include(router.urls)),
]
