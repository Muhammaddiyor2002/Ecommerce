from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, WebhookView

router = DefaultRouter()
router.register(r"", PaymentViewSet, basename="payments")

urlpatterns = [
    path("webhooks/<str:provider_code>/", WebhookView.as_view(), name="payments-webhook"),
    path("", include(router.urls)),
]
