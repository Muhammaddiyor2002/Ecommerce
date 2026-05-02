from __future__ import annotations

import pytest
from apps.inventory.services import (
    OutOfStockError,
    commit_sale,
    get_available,
    release_reservation,
    reserve_stock,
)


@pytest.mark.django_db
def test_reserve_then_commit(catalog_seed):
    v = catalog_seed["variant"]
    assert get_available(variant_id=str(v.id)) == 50

    snap = reserve_stock(variant_id=str(v.id), quantity=3, reference="o1")
    assert snap.reserved == 3
    assert get_available(variant_id=str(v.id)) == 47

    commit_sale(variant_id=str(v.id), quantity=3, reference="o1")
    # After commit, reserved freed but on_hand decreased
    assert get_available(variant_id=str(v.id)) == 47


@pytest.mark.django_db
def test_reserve_then_release(catalog_seed):
    v = catalog_seed["variant"]
    reserve_stock(variant_id=str(v.id), quantity=5)
    assert get_available(variant_id=str(v.id)) == 45
    release_reservation(variant_id=str(v.id), quantity=5)
    assert get_available(variant_id=str(v.id)) == 50


@pytest.mark.django_db
def test_oversell_blocked(catalog_seed):
    v = catalog_seed["variant"]
    with pytest.raises(OutOfStockError):
        reserve_stock(variant_id=str(v.id), quantity=1000)
