"""Inventory service layer — atomic, race-safe operations."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .models import Stock, StockMovement, Warehouse


class OutOfStockError(Exception):
    """Raised when there is not enough available stock to satisfy a request."""


@dataclass(slots=True)
class StockSnapshot:
    variant_id: str
    available: int
    on_hand: int
    reserved: int


def get_available(variant_id: str) -> int:
    qs = Stock.objects.filter(variant_id=variant_id)
    return sum(s.available for s in qs)


@transaction.atomic
def reserve_stock(*, variant_id: str, quantity: int, reference: str = "") -> StockSnapshot:
    """Reserve ``quantity`` units across warehouses by priority."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    rows = (
        Stock.objects.select_for_update()
        .filter(variant_id=variant_id, warehouse__is_active=True)
        .select_related("warehouse")
        .order_by("warehouse__priority")
    )
    remaining = quantity
    snapshot_on_hand = 0
    snapshot_reserved = 0

    for stock in rows:
        snapshot_on_hand += stock.on_hand
        if remaining <= 0:
            snapshot_reserved += stock.reserved
            continue
        take = min(stock.available, remaining)
        if take > 0:
            stock.reserved += take
            stock.save(update_fields=["reserved", "updated_at"])
            StockMovement.objects.create(
                stock=stock,
                quantity=-take,
                reason=StockMovement.Reason.RESERVATION,
                reference=reference,
            )
            remaining -= take
        snapshot_reserved += stock.reserved

    if remaining > 0:
        raise OutOfStockError(f"insufficient stock for variant {variant_id}: short by {remaining}")

    return StockSnapshot(
        variant_id=str(variant_id),
        available=snapshot_on_hand - snapshot_reserved,
        on_hand=snapshot_on_hand,
        reserved=snapshot_reserved,
    )


@transaction.atomic
def release_reservation(*, variant_id: str, quantity: int, reference: str = "") -> None:
    rows = (
        Stock.objects.select_for_update()
        .filter(variant_id=variant_id, reserved__gt=0)
        .order_by("-reserved")
    )
    remaining = quantity
    for stock in rows:
        if remaining <= 0:
            break
        give_back = min(stock.reserved, remaining)
        if give_back:
            stock.reserved -= give_back
            stock.save(update_fields=["reserved", "updated_at"])
            StockMovement.objects.create(
                stock=stock,
                quantity=give_back,
                reason=StockMovement.Reason.RESERVATION_RELEASE,
                reference=reference,
            )
            remaining -= give_back


@transaction.atomic
def commit_sale(*, variant_id: str, quantity: int, reference: str) -> None:
    """Convert reservations into actual outflow when an order is paid."""
    rows = (
        Stock.objects.select_for_update()
        .filter(variant_id=variant_id, reserved__gt=0)
        .order_by("-reserved")
    )
    remaining = quantity
    for stock in rows:
        if remaining <= 0:
            break
        take = min(stock.reserved, stock.on_hand, remaining)
        if take:
            stock.reserved -= take
            stock.on_hand -= take
            stock.save(update_fields=["reserved", "on_hand", "updated_at"])
            StockMovement.objects.create(
                stock=stock,
                quantity=-take,
                reason=StockMovement.Reason.SALE,
                reference=reference,
            )
            remaining -= take
    if remaining > 0:
        raise OutOfStockError(
            f"could not commit {quantity} for variant {variant_id} (short by {remaining})"
        )


@transaction.atomic
def adjust_stock(*, variant_id: str, warehouse_code: str, delta: int, note: str = "") -> Stock:
    warehouse = Warehouse.objects.get(code=warehouse_code)
    stock, _ = Stock.objects.select_for_update().get_or_create(
        variant_id=variant_id, warehouse=warehouse
    )
    stock.on_hand = max(stock.on_hand + delta, 0)
    stock.save(update_fields=["on_hand", "updated_at"])
    StockMovement.objects.create(
        stock=stock,
        quantity=delta,
        reason=StockMovement.Reason.ADJUSTMENT,
        note=note,
    )
    return stock
