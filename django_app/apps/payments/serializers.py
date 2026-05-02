from __future__ import annotations

from rest_framework import serializers

from .models import Payment, Refund
from .providers import REGISTRY


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "provider",
            "status",
            "amount",
            "currency",
            "provider_reference",
            "provider_intent_id",
            "redirect_url",
            "created_at",
            "updated_at",
        )


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ("id", "payment", "amount", "reason", "provider_reference", "created_at")


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=sorted(REGISTRY.keys()))
    success_url = serializers.URLField(required=False, allow_blank=True)
    cancel_url = serializers.URLField(required=False, allow_blank=True)
