"""Reusable DRF permission classes implementing RBAC."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework.permissions import BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class HasRole(BasePermission):
    """Allow access when the user has any of the required roles.

    Subclasses set ``required_roles`` (set of role codes).
    """

    required_roles: tuple[str, ...] = ()

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        user_roles = {r.code for r in getattr(user, "roles", []).all()}  # type: ignore[union-attr]
        return any(r in user_roles for r in self.required_roles)


class IsCustomer(HasRole):
    required_roles = ("customer",)


class IsStaff(HasRole):
    required_roles = ("staff", "admin")


class IsAdmin(HasRole):
    required_roles = ("admin",)


class IsVendor(HasRole):
    required_roles = ("vendor",)


class IsOwnerOrStaff(BasePermission):
    """Object-level: allow access if the user owns the object or is staff."""

    owner_field = "user"

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        owner = getattr(obj, self.owner_field, None)
        return owner == user
