from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.cart.services import get_or_create_cart
from apps.core.permissions import IsOwnerOrStaff

from .models import Order
from .serializers import CheckoutSerializer, OrderSerializer
from .services import CheckoutError, CheckoutInput, create_order_from_cart, transition_status


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "user"

    def get_queryset(self):
        qs = (
            Order.objects.all()
            .select_related("user")
            .prefetch_related("items", "events")
            .order_by("-created_at")
        )
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs
        return qs.filter(user=self.request.user)

    @action(
        detail=False, methods=["post"], url_path="checkout", throttle_classes=[ScopedRateThrottle]
    )
    def checkout(self, request):
        self.throttle_scope = "checkout"
        ser = CheckoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session_key = request.session.session_key or ""
        if not session_key and not request.user.is_authenticated:
            request.session.create()
            session_key = request.session.session_key
        cart = get_or_create_cart(user=request.user, session_key=session_key)
        try:
            order = create_order_from_cart(
                cart=cart,
                user=request.user,
                payload=CheckoutInput(**ser.validated_data),
            )
        except CheckoutError as exc:
            return Response(
                {"error": {"code": "checkout_failed", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            transition_status(
                order=order,
                new_status=Order.Status.CANCELLED,
                actor=request.user,
                message="cancelled by user",
            )
        except CheckoutError as exc:
            return Response(
                {"error": {"code": "invalid_transition", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        order.refresh_from_db()
        return Response(OrderSerializer(order).data)
