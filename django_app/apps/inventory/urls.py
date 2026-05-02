from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StockMovementViewSet, StockViewSet, WarehouseViewSet

router = DefaultRouter()
router.register(r"warehouses", WarehouseViewSet, basename="warehouses")
router.register(r"stocks", StockViewSet, basename="stocks")
router.register(r"movements", StockMovementViewSet, basename="movements")

urlpatterns = [path("", include(router.urls))]
