from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_anonymous_can_add_to_cart(api_client, catalog_seed):
    v = catalog_seed["variant"]
    res = api_client.post(
        "/api/v1/cart/items/",
        {
            "variant_id": str(v.id),
            "quantity": 2,
        },
        format="json",
    )
    assert res.status_code == 201, res.content
    cart = res.data
    assert cart["total_items"] == 2
    assert len(cart["items"]) == 1


@pytest.mark.django_db
def test_user_cart_persists(auth_client, catalog_seed):
    v = catalog_seed["variant"]
    auth_client.post(
        "/api/v1/cart/items/",
        {
            "variant_id": str(v.id),
            "quantity": 1,
        },
        format="json",
    )
    res = auth_client.get("/api/v1/cart/")
    assert res.status_code == 200
    assert res.data["total_items"] == 1


@pytest.mark.django_db
def test_cart_rejects_oversell(api_client, catalog_seed):
    v = catalog_seed["variant"]
    res = api_client.post(
        "/api/v1/cart/items/",
        {
            "variant_id": str(v.id),
            "quantity": 10_000,
        },
        format="json",
    )
    assert res.status_code == 409
    assert res.data["error"]["code"] == "out_of_stock"
