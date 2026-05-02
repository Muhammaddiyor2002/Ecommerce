"""Race-condition tests for stock reservations.

We can't run *true* concurrent transactions on SQLite easily, but we can
verify correctness by interleaving reservations sequentially and asserting
that the invariants hold under repeated calls.
"""

from __future__ import annotations

import pytest
from apps.inventory.services import OutOfStockError, get_available, reserve_stock


@pytest.mark.django_db
def test_reservations_are_exact_under_repeated_calls(catalog_seed):
    v = catalog_seed["variant"]
    initial = get_available(variant_id=str(v.id))
    for _ in range(initial):
        reserve_stock(variant_id=str(v.id), quantity=1)
    assert get_available(variant_id=str(v.id)) == 0
    with pytest.raises(OutOfStockError):
        reserve_stock(variant_id=str(v.id), quantity=1)
