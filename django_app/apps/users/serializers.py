"""DRF serializers for auth and user-facing endpoints."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, Role

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name", "description")


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_active",
            "is_staff",
            "email_verified_at",
            "phone_verified_at",
            "roles",
            "created_at",
        )
        read_only_fields = (
            "id",
            "is_active",
            "is_staff",
            "email_verified_at",
            "phone_verified_at",
            "created_at",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "phone")

    def create(self, validated: dict[str, Any]) -> Any:
        user = User.objects.create_user(**validated)
        try:
            customer = Role.objects.get(code="customer")
            user.roles.add(customer)
        except Role.DoesNotExist:
            pass
        return user


class NovaTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Embed minimal user info in the access token claims."""

    @classmethod
    def get_token(cls, user: Any) -> RefreshToken:
        token = super().get_token(user)
        token["email"] = user.email
        token["roles"] = list(user.roles.values_list("code", flat=True))
        token["is_staff"] = user.is_staff
        return token


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "label",
            "kind",
            "full_name",
            "phone",
            "country",
            "region",
            "city",
            "street",
            "apartment",
            "postal_code",
            "is_default",
            "location",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
