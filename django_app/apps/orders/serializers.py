from __future__ import annotations

from rest_framework import serializers

from .models import Order, OrderEvent, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "variant",
            "sku",
            "name_snapshot",
            "attributes_snapshot",
            "quantity",
            "unit_price",
            "line_total",
        )


class OrderEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEvent
        fields = ("id", "code", "message", "actor", "payload", "created_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "user",
            "email_snapshot",
            "phone_snapshot",
            "status",
            "currency",
            "subtotal",
            "shipping_total",
            "tax_total",
            "discount_total",
            "grand_total",
            "coupon_code",
            "shipping_address",
            "billing_address",
            "payment_provider",
            "payment_reference",
            "paid_at",
            "cancelled_at",
            "refunded_at",
            "notes_customer",
            "metadata",
            "items",
            "events",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=24)
    shipping_address = serializers.JSONField()
    billing_address = serializers.JSONField(required=False)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=64)
    shipping_method = serializers.ChoiceField(
        choices=("standard", "express", "pickup"),
        default="standard",
    )
    notes_customer = serializers.CharField(required=False, allow_blank=True)
