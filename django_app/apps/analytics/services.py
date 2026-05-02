"""Live and batch analytics queries."""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal

from django.db.models import (
    Avg,
    Count,
    DecimalField,
    F,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.cart.models import Cart
from apps.orders.models import Order, OrderItem


def revenue_today() -> Decimal:
    today = timezone.now().date()
    agg = Order.objects.filter(
        status=Order.Status.PAID,
        paid_at__date=today,
    ).aggregate(
        total=Coalesce(Sum("grand_total"), Value(Decimal("0.00"), output_field=DecimalField()))
    )
    return agg["total"] or Decimal("0.00")


def orders_today() -> dict:
    today = timezone.now().date()
    qs = Order.objects.filter(created_at__date=today)
    return {
        "total": qs.count(),
        "paid": qs.filter(status=Order.Status.PAID).count(),
        "cancelled": qs.filter(status=Order.Status.CANCELLED).count(),
    }


def average_order_value(days: int = 30) -> Decimal:
    since = timezone.now() - _dt.timedelta(days=days)
    agg = Order.objects.filter(
        status=Order.Status.PAID,
        paid_at__gte=since,
    ).aggregate(
        avg=Coalesce(Avg("grand_total"), Value(Decimal("0.00"), output_field=DecimalField()))
    )
    return Decimal(str(agg["avg"] or 0)).quantize(Decimal("0.01"))


def top_products(limit: int = 10, days: int = 30) -> list[dict]:
    since = timezone.now() - _dt.timedelta(days=days)
    qs = (
        OrderItem.objects.filter(order__status=Order.Status.PAID, order__paid_at__gte=since)
        .values("variant__product_id", "variant__product__name")
        .annotate(qty=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity")))
        .order_by("-qty")[:limit]
    )
    return [
        {
            "product_id": str(r["variant__product_id"]),
            "name": r["variant__product__name"],
            "qty": r["qty"],
            "revenue": str(r["revenue"]),
        }
        for r in qs
    ]


def abandoned_carts(idle_minutes: int = 60, limit: int = 100) -> list[dict]:
    cutoff = timezone.now() - _dt.timedelta(minutes=idle_minutes)
    qs = (
        Cart.objects.filter(
            last_active_at__lt=cutoff,
            items__isnull=False,
        )
        .annotate(item_count=Count("items"))
        .filter(item_count__gt=0)
        .distinct()
        .order_by("-last_active_at")[:limit]
    )
    out = []
    for c in qs:
        out.append(
            {
                "cart_id": str(c.id),
                "user": c.user.email if c.user_id else None,
                "last_active_at": c.last_active_at.isoformat(),
                "item_count": c.item_count,
                "subtotal": str(c.subtotal()),
            }
        )
    return out


def revenue_timeseries(days: int = 30) -> list[dict]:
    since = (timezone.now() - _dt.timedelta(days=days)).date()
    qs = (
        Order.objects.filter(status=Order.Status.PAID, paid_at__date__gte=since)
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(revenue=Sum("grand_total"), orders=Count("id"))
        .order_by("day")
    )
    return [
        {"day": r["day"].isoformat(), "revenue": str(r["revenue"]), "orders": r["orders"]}
        for r in qs
    ]


def low_stock_alerts(threshold: int | None = None) -> int:
    """Count of stocks below their low threshold."""
    from apps.inventory.models import Stock

    qs = Stock.objects.all()
    return sum(1 for s in qs if s.is_low)
