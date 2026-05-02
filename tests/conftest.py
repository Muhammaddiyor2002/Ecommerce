"""Shared fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest
from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.inventory.models import Stock, Warehouse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def password() -> str:
    return "Sup3r-Secret-XYZ!"


@pytest.fixture
def user(db, password):
    User = get_user_model()
    return User.objects.create_user(
        email="alice@example.com",
        password=password,
        first_name="Alice",
    )


@pytest.fixture
def staff_user(db, password):
    User = get_user_model()
    u = User.objects.create_user(
        email="staff@example.com",
        password=password,
        first_name="Staff",
    )
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def auth_client(api_client, user, password):
    res = api_client.post(
        "/api/v1/auth/login/", {"email": user.email, "password": password}, format="json"
    )
    assert res.status_code == 200, res.content
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user, password):
    res = api_client.post(
        "/api/v1/auth/login/", {"email": staff_user.email, "password": password}, format="json"
    )
    assert res.status_code == 200, res.content
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return api_client


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(code="main", name="Main", is_active=True)


@pytest.fixture
def catalog_seed(db, warehouse):
    brand = Brand.objects.create(slug="nova", name="Nova")
    category = Category.objects.create(slug="apparel", name="Apparel")
    product = Product.objects.create(
        slug="nova-tee",
        name="Nova Tee",
        brand=brand,
        short_description="Soft cotton tee",
        status=Product.Status.ACTIVE,
    )
    product.categories.add(category)
    variant = ProductVariant.objects.create(
        product=product,
        sku="NOVA-TEE-M",
        name="M",
        price=Decimal("19.99"),
        compare_at_price=Decimal("24.99"),
        is_default=True,
        is_active=True,
        attributes_snapshot={"size": "M", "color": "black"},
    )
    Stock.objects.create(variant=variant, warehouse=warehouse, on_hand=50)
    return {
        "brand": brand,
        "category": category,
        "product": product,
        "variant": variant,
        "warehouse": warehouse,
    }
