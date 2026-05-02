from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsStaff

from .models import Coupon
from .serializers import CouponSerializer


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all().order_by("-created_at")
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    @action(detail=False, methods=["get"], url_path=r"validate/(?P<code>[^/.]+)")
    def validate_code(self, request, code=None):
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({"valid": False, "reason": "not_found"}, status=404)
        return Response(
            {
                "valid": coupon.is_valid_now(),
                "coupon": CouponSerializer(coupon).data,
            }
        )
