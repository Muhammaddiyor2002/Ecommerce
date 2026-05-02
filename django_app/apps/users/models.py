"""User & RBAC models.

We use a custom User with email-as-username, a Role table for RBAC, and an
Address book for shipping/billing destinations.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedUUIDModel


class Role(TimeStampedUUIDModel):
    """A named role assigned to users for RBAC checks."""

    code = models.SlugField(unique=True, max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text=_("System-managed role (cannot be deleted from admin)."),
    )

    class Meta:
        db_table = "users_role"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra: Any) -> User:
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        if not extra.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedUUIDModel):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=24, blank=True, db_index=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    roles = models.ManyToManyField(Role, related_name="users", blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["is_active", "is_staff"]),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def has_role(self, code: str) -> bool:
        return self.roles.filter(code=code).exists()


class Address(TimeStampedUUIDModel):
    class Kind(models.TextChoices):
        SHIPPING = "shipping", _("Shipping")
        BILLING = "billing", _("Billing")
        BOTH = "both", _("Shipping & Billing")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=64, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.SHIPPING)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=24)
    country = models.CharField(max_length=2, default="UZ")
    region = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120)
    street = models.CharField(max_length=255)
    apartment = models.CharField(max_length=64, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    location = models.JSONField(default=dict, blank=True, help_text="lat/lng if available")

    class Meta:
        db_table = "users_address"
        indexes = [
            models.Index(fields=["user", "kind"]),
            models.Index(fields=["user", "is_default"]),
        ]
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name}, {self.city}"


class Wishlist(TimeStampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wishlist")
    products = models.ManyToManyField("catalog.Product", related_name="wishlists", blank=True)

    class Meta:
        db_table = "users_wishlist"
