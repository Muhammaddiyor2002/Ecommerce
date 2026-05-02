from __future__ import annotations

from decimal import Decimal

import pytest
from apps.coupons.models import Coupon


@pytest.mark.django_db
def test_percent_coupon_calculation():
    c = Coupon.objects.create(
        code="SALE10",
        kind=Coupon.Kind.PERCENT,
        value=Decimal("10"),
        min_subtotal=Decimal("0"),
    )
    assert c.calculate_discount(Decimal("100.00")) == Decimal("10.00")


@pytest.mark.django_db
def test_percent_coupon_caps():
    c = Coupon.objects.create(
        code="BIG",
        kind=Coupon.Kind.PERCENT,
        value=Decimal("50"),
        min_subtotal=Decimal("0"),
        max_discount=Decimal("20"),
    )
    assert c.calculate_discount(Decimal("100.00")) == Decimal("20.00")


@pytest.mark.django_db
def test_fixed_coupon_capped_to_subtotal():
    c = Coupon.objects.create(
        code="FIVE",
        kind=Coupon.Kind.FIXED,
        value=Decimal("5"),
    )
    assert c.calculate_discount(Decimal("3.00")) == Decimal("3.00")


@pytest.mark.django_db
def test_min_subtotal_block():
    c = Coupon.objects.create(
        code="MIN50",
        kind=Coupon.Kind.PERCENT,
        value=Decimal("10"),
        min_subtotal=Decimal("50"),
    )
    assert c.calculate_discount(Decimal("10.00")) == Decimal("0.00")
