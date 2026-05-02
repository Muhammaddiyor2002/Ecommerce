from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_healthz(api_client: APIClient):
    res = api_client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
