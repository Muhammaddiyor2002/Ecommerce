from __future__ import annotations

import pytest
from apps.orders.models import Order
from apps.orders.services import (
    CheckoutError,
    CheckoutInput,
    create_order_from_cart,
    transition_status,
)


@pytest.mark.django_db
def test_checkout_creates_order(auth_client, user, catalog_seed):
    v = catalog_seed["variant"]
    auth_client.post("/api/v1/cart/items/", {"variant_id": str(v.id), "quantity": 2}, format="json")
    res = auth_client.post(
        "/api/v1/orders/checkout/",
        {
            "email": user.email,
            "phone": "+10000000000",
            "shipping_address": {"line1": "1 Main", "city": "Tashkent", "country": "UZ"},
            "shipping_method": "standard",
        },
        format="json",
    )
    assert res.status_code == 201, res.content
    assert res.data["status"] == Order.Status.PENDING.value
    assert res.data["grand_total"] is not None


@pytest.mark.django_db
def test_status_machine_invalid_transition(catalog_seed, user, db):
    from apps.cart.services import add_item, get_or_create_cart

    cart = get_or_create_cart(user=user, session_key="t")
    add_item(cart=cart, variant_id=str(catalog_seed["variant"].id), quantity=1)
    order = create_order_from_cart(
        cart=cart,
        user=user,
        payload=CheckoutInput(
            email=user.email,
            phone="x",
            shipping_address={"city": "x"},
        ),
    )
    transition_status(order=order, new_status=Order.Status.PAID)
    # Cannot go from PAID directly back to PENDING
    with pytest.raises(CheckoutError):
        transition_status(order=order, new_status=Order.Status.PENDING)


@pytest.mark.django_db
def test_cancel_order_releases_stock(auth_client, user, catalog_seed):
    from apps.cart.services import add_item, get_or_create_cart
    from apps.inventory.services import get_available

    cart = get_or_create_cart(user=user, session_key="t")
    add_item(cart=cart, variant_id=str(catalog_seed["variant"].id), quantity=4)
    order = create_order_from_cart(
        cart=cart,
        user=user,
        payload=CheckoutInput(
            email=user.email,
            phone="x",
            shipping_address={"city": "x"},
        ),
    )
    available_before = get_available(variant_id=str(catalog_seed["variant"].id))
    transition_status(order=order, new_status=Order.Status.CANCELLED)
    available_after = get_available(variant_id=str(catalog_seed["variant"].id))
    assert available_after == available_before + 4
