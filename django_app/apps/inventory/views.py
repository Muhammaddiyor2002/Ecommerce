from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsStaff

from .models import Stock, StockMovement, Warehouse
from .serializers import StockMovementSerializer, StockSerializer, WarehouseSerializer
from .services import adjust_stock


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsStaff]


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related("variant", "warehouse").order_by("-updated_at")
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    @action(detail=False, methods=["post"], url_path="adjust")
    def adjust(self, request):
        variant_id = request.data["variant_id"]
        warehouse_code = request.data["warehouse_code"]
        delta = int(request.data["delta"])
        note = request.data.get("note", "")
        stock = adjust_stock(
            variant_id=variant_id,
            warehouse_code=warehouse_code,
            delta=delta,
            note=note,
        )
        return Response(StockSerializer(stock).data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related("stock").order_by("-created_at")
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, IsStaff]
