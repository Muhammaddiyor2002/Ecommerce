from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import ProductVariant

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "variant", "sku", "product_name", "quantity", "unit_price", "line_total")
        read_only_fields = ("id", "unit_price")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "id",
            "user",
            "session_key",
            "currency",
            "items",
            "coupon",
            "subtotal",
            "total_items",
            "metadata",
            "last_active_at",
        )
        read_only_fields = (
            "id",
            "user",
            "session_key",
            "items",
            "subtotal",
            "total_items",
            "last_active_at",
        )

    def get_subtotal(self, obj):
        return obj.subtotal()

    def get_total_items(self, obj):
        return obj.total_items()


class AddItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_variant_id(self, val):
        if not ProductVariant.objects.filter(pk=val, is_active=True).exists():
            raise serializers.ValidationError("variant not found or inactive")
        return val


class UpdateItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)
