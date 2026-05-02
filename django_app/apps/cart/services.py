"""Cart service layer — atomic, validates stock at modification time."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.catalog.models import ProductVariant
from apps.inventory.services import OutOfStockError, get_available

from .models import Cart, CartItem


@transaction.atomic
def get_or_create_cart(*, user=None, session_key: str = "") -> Cart:
    if user and user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=user, defaults={"currency": "USD"})
        return cart
    if not session_key:
        raise ValueError("session_key required for anonymous carts")
    cart, _ = Cart.objects.get_or_create(
        session_key=session_key, user=None, defaults={"currency": "USD"}
    )
    return cart


@transaction.atomic
def add_item(*, cart: Cart, variant_id: str, quantity: int = 1) -> CartItem:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    variant = ProductVariant.objects.select_related("product").get(pk=variant_id, is_active=True)

    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart,
        variant=variant,
        defaults={"quantity": 0, "unit_price": variant.price},
    )
    new_qty = item.quantity + quantity
    available = get_available(variant_id=str(variant_id))
    if new_qty > available:
        raise OutOfStockError(f"requested {new_qty}, only {available} available for {variant.sku}")
    item.quantity = new_qty
    item.unit_price = variant.price
    item.save()
    return item


@transaction.atomic
def update_item(*, cart: Cart, item_id: str, quantity: int) -> CartItem | None:
    item = CartItem.objects.select_for_update().get(pk=item_id, cart=cart)
    if quantity <= 0:
        item.delete()
        return None
    available = get_available(variant_id=str(item.variant_id))
    if quantity > available:
        raise OutOfStockError(f"only {available} available for {item.variant.sku}")
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item


@transaction.atomic
def remove_item(*, cart: Cart, item_id: str) -> None:
    CartItem.objects.filter(pk=item_id, cart=cart).delete()


@transaction.atomic
def clear_cart(*, cart: Cart) -> None:
    cart.items.all().delete()
    cart.coupon = None
    cart.save(update_fields=["coupon"])


@transaction.atomic
def merge_anonymous_into_user(*, session_key: str, user: Any) -> Cart | None:
    """Merge a guest cart into the user's cart on login."""
    if not session_key:
        return None
    try:
        anon = Cart.objects.select_for_update().get(session_key=session_key, user=None)
    except Cart.DoesNotExist:
        return None

    user_cart, _ = Cart.objects.select_for_update().get_or_create(
        user=user, defaults={"currency": anon.currency}
    )
    for item in anon.items.all():
        existing = user_cart.items.filter(variant=item.variant).first()
        if existing:
            existing.quantity += item.quantity
            existing.unit_price = item.variant.price
            existing.save()
        else:
            CartItem.objects.create(
                cart=user_cart,
                variant=item.variant,
                quantity=item.quantity,
                unit_price=item.variant.price,
            )
    anon.delete()
    return user_cart
