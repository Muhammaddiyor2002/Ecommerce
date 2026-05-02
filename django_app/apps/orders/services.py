"""Order service layer.

Coordinates: cart -> order conversion, status transitions, stock commits,
post-transition side effects (notifications, realtime broadcasts).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart
from apps.coupons.models import Coupon
from apps.inventory.services import (
    OutOfStockError,
    commit_sale,
    release_reservation,
    reserve_stock,
)

from .models import Order, OrderEvent, OrderItem


@dataclass(slots=True)
class CheckoutInput:
    email: str
    phone: str
    shipping_address: dict
    billing_address: dict | None = None
    coupon_code: str = ""
    shipping_method: str = "standard"
    notes_customer: str = ""


class CheckoutError(Exception):
    pass


def _calculate_shipping(method: str, subtotal: Decimal) -> Decimal:
    if subtotal >= Decimal("200.00"):
        return Decimal("0.00")
    return {
        "standard": Decimal("9.99"),
        "express": Decimal("19.99"),
        "pickup": Decimal("0.00"),
    }.get(method, Decimal("9.99"))


def _calculate_tax(subtotal: Decimal, region: str = "") -> Decimal:
    """Simple flat 0% by default; replace with provider in production."""
    return Decimal("0.00")


@transaction.atomic
def create_order_from_cart(*, cart: Cart, user: Any, payload: CheckoutInput) -> Order:
    if not cart.items.exists():
        raise CheckoutError("cart is empty")

    subtotal = cart.subtotal()
    discount = Decimal("0.00")
    coupon: Coupon | None = None
    if payload.coupon_code:
        try:
            coupon = Coupon.objects.select_for_update().get(code__iexact=payload.coupon_code)
        except Coupon.DoesNotExist as exc:
            raise CheckoutError("invalid coupon") from exc
        if not coupon.is_valid_now():
            raise CheckoutError("coupon expired or inactive")
        discount = coupon.calculate_discount(subtotal)

    shipping = _calculate_shipping(payload.shipping_method, subtotal - discount)
    tax = _calculate_tax(subtotal - discount + shipping)
    grand = (subtotal - discount + shipping + tax).quantize(Decimal("0.01"))

    order = Order.objects.create(
        user=user if (user and user.is_authenticated) else None,
        email_snapshot=payload.email,
        phone_snapshot=payload.phone,
        status=Order.Status.PENDING,
        currency=cart.currency,
        subtotal=subtotal,
        discount_total=discount,
        shipping_total=shipping,
        tax_total=tax,
        grand_total=grand,
        coupon_code=coupon.code if coupon else "",
        shipping_address=payload.shipping_address,
        billing_address=payload.billing_address or payload.shipping_address,
        notes_customer=payload.notes_customer,
        metadata={"shipping_method": payload.shipping_method},
    )

    # Reserve stock + write items
    for item in cart.items.select_related("variant", "variant__product"):
        try:
            reserve_stock(
                variant_id=str(item.variant_id),
                quantity=item.quantity,
                reference=str(order.id),
            )
        except OutOfStockError as exc:
            raise CheckoutError(str(exc)) from exc

        OrderItem.objects.create(
            order=order,
            variant=item.variant,
            sku=item.variant.sku,
            name_snapshot=item.variant.product.name,
            attributes_snapshot=item.variant.attributes_snapshot,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )

    if coupon:
        coupon.used_count += 1
        coupon.save(update_fields=["used_count"])

    OrderEvent.objects.create(
        order=order,
        code="created",
        message="Order created",
        actor=user if user and user.is_authenticated else None,
    )

    # Empty the cart now that the order is materialised
    cart.items.all().delete()
    cart.coupon = None
    cart.save(update_fields=["coupon"])

    return order


@transaction.atomic
def transition_status(
    *, order: Order, new_status: Order.Status, actor: Any | None = None, message: str = ""
) -> Order:
    order = Order.objects.select_for_update().get(pk=order.pk)
    if not order.can_transition_to(new_status):
        raise CheckoutError(
            f"cannot transition order {order.number} from {order.status} to {new_status}"
        )
    order.status = new_status
    update_fields = ["status", "updated_at"]

    if new_status == Order.Status.PAID:
        order.paid_at = timezone.now()
        update_fields.append("paid_at")
        # Convert reservations into actual outflows
        for item in order.items.all():
            if item.variant_id:
                commit_sale(
                    variant_id=str(item.variant_id),
                    quantity=item.quantity,
                    reference=str(order.id),
                )
    elif new_status == Order.Status.CANCELLED:
        order.cancelled_at = timezone.now()
        update_fields.append("cancelled_at")
        # Release reservations
        for item in order.items.all():
            if item.variant_id:
                release_reservation(
                    variant_id=str(item.variant_id),
                    quantity=item.quantity,
                    reference=str(order.id),
                )
    elif new_status == Order.Status.REFUNDED:
        order.refunded_at = timezone.now()
        update_fields.append("refunded_at")

    order.save(update_fields=update_fields)
    OrderEvent.objects.create(
        order=order,
        code=f"status:{new_status}",
        message=message or f"Status changed to {new_status}",
        actor=actor,
    )
    return order
