from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order

from .models import Payment
from .serializers import CreatePaymentSerializer, PaymentSerializer
from .services import create_payment, handle_webhook

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Payment.objects.select_related("order").order_by("-created_at")
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs
        return qs.filter(order__user=self.request.user)

    @action(detail=False, methods=["post"], url_path="create")
    def create_for_order(self, request):
        ser = CreatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order = get_object_or_404(Order, pk=ser.validated_data["order_id"])
        # Permission: only owner or staff can pay
        if not request.user.is_staff and order.user_id != request.user.id:
            return Response(
                {"error": {"code": "forbidden", "message": "not your order"}},
                status=status.HTTP_403_FORBIDDEN,
            )
        payment = create_payment(
            order=order,
            provider_code=ser.validated_data["provider"],
            success_url=ser.validated_data.get("success_url", ""),
            cancel_url=ser.validated_data.get("cancel_url", ""),
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class WebhookView(APIView):
    """Public, unauthenticated entrypoint for provider webhooks.

    Each provider verifies its own signature inside ``handle_webhook``.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request, provider_code: str):
        body = request.body or b""
        headers = dict(request.headers.items())
        result = handle_webhook(provider_code=provider_code, headers=headers, body=body)
        if not result.get("accepted", False):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)
