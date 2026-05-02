from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CouponViewSet

router = DefaultRouter()
router.register(r"", CouponViewSet, basename="coupons")

urlpatterns = [path("", include(router.urls))]
