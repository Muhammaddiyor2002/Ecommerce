from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaff

from . import services


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        return Response(
            {
                "revenue_today": services.revenue_today(),
                "orders_today": services.orders_today(),
                "average_order_value_30d": services.average_order_value(30),
                "top_products_30d": services.top_products(),
                "abandoned_carts": services.abandoned_carts(),
                "revenue_timeseries_30d": services.revenue_timeseries(),
                "low_stock_alerts": services.low_stock_alerts(),
            }
        )
