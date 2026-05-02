from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Address, Role, User, Wishlist


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_system", "created_at")
    list_filter = ("is_system",)
    search_fields = ("code", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active", "is_superuser", "roles")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-created_at",)
    filter_horizontal = ("roles", "groups", "user_permissions")
    readonly_fields = (
        "id",
        "last_login",
        "created_at",
        "updated_at",
        "email_verified_at",
        "phone_verified_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "roles",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Verification", {"fields": ("email_verified_at", "phone_verified_at", "last_login_ip")}),
        ("Timestamps", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "kind", "city", "country", "is_default")
    list_filter = ("kind", "country", "is_default")
    search_fields = ("user__email", "full_name", "city", "street")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")
