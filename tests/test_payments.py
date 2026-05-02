from __future__ import annotations

import pytest
from apps.cart.services import add_item, get_or_create_cart
from apps.orders.services import CheckoutInput, create_order_from_cart
from apps.payments.models import Payment
from apps.payments.providers import get_provider
from apps.payments.services import create_payment


@pytest.mark.django_db
def test_manual_provider_creates_charge(user, catalog_seed):
    cart = get_or_create_cart(user=user, session_key="x")
    add_item(cart=cart, variant_id=str(catalog_seed["variant"].id), quantity=1)
    order = create_order_from_cart(
        cart=cart,
        user=user,
        payload=CheckoutInput(email=user.email, phone="x", shipping_address={}),
    )
    payment = create_payment(order=order, provider_code="manual")
    assert payment.status == Payment.Status.PENDING.value
    assert payment.provider_reference.startswith("manual:")


@pytest.mark.django_db
def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("does-not-exist")
