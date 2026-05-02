from __future__ import annotations

from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "name",
            "kind",
            "value",
            "min_subtotal",
            "max_discount",
            "max_uses",
            "used_count",
            "per_user_limit",
            "starts_at",
            "ends_at",
            "is_active",
            "is_valid_now",
        )
        read_only_fields = ("id", "used_count", "is_valid_now")
