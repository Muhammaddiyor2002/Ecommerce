from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_register(api_client):
    res = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "bob@example.com",
            "password": "Sup3r-Secret-XYZ!",
            "first_name": "Bob",
        },
        format="json",
    )
    assert res.status_code == 201, res.content
    User = get_user_model()
    assert User.objects.filter(email="bob@example.com").exists()


@pytest.mark.django_db
def test_login_ok(api_client, user, password):
    res = api_client.post(
        "/api/v1/auth/login/",
        {
            "email": user.email,
            "password": password,
        },
        format="json",
    )
    assert res.status_code == 200, res.content
    assert "access" in res.data
    assert "refresh" in res.data


@pytest.mark.django_db
def test_login_bad_password(api_client, user):
    res = api_client.post(
        "/api/v1/auth/login/",
        {
            "email": user.email,
            "password": "WRONG!",
        },
        format="json",
    )
    assert res.status_code == 401


@pytest.mark.django_db
def test_me_endpoint(auth_client):
    res = auth_client.get("/api/v1/me/")
    assert res.status_code == 200, res.content
    assert res.data["email"] == "alice@example.com"


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    res = api_client.get("/api/v1/me/")
    assert res.status_code == 401
