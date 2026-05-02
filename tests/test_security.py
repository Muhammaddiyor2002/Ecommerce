from __future__ import annotations

import pytest
from apps.cart.services import add_item, get_or_create_cart
from apps.orders.services import CheckoutInput, create_order_from_cart


@pytest.mark.django_db
def test_user_cannot_view_others_orders(api_client, user, catalog_seed, password):
    """Users may only see their own orders, never other users' orders."""
    cart = get_or_create_cart(user=user, session_key="x")
    add_item(cart=cart, variant_id=str(catalog_seed["variant"].id), quantity=1)
    order = create_order_from_cart(
        cart=cart,
        user=user,
        payload=CheckoutInput(email=user.email, phone="x", shipping_address={}),
    )

    from django.contrib.auth import get_user_model

    User = get_user_model()
    intruder = User.objects.create_user(email="evil@example.com", password=password)
    res = api_client.post(
        "/api/v1/auth/login/", {"email": intruder.email, "password": password}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    res = api_client.get(f"/api/v1/orders/{order.id}/")
    assert res.status_code in {404, 403}


@pytest.mark.django_db
def test_protected_endpoints_reject_anonymous(api_client):
    res = api_client.get("/api/v1/orders/")
    assert res.status_code == 401
