from __future__ import annotations

from rest_framework import serializers

from .models import Stock, StockMovement, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ("id", "code", "name", "address", "is_active", "priority")


class StockSerializer(serializers.ModelSerializer):
    available = serializers.IntegerField(read_only=True)
    is_low = serializers.BooleanField(read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)

    class Meta:
        model = Stock
        fields = (
            "id",
            "variant",
            "sku",
            "warehouse",
            "warehouse_code",
            "on_hand",
            "reserved",
            "available",
            "safety_buffer",
            "low_stock_threshold",
            "is_low",
        )


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ("id", "stock", "quantity", "reason", "reference", "note", "created_at")
