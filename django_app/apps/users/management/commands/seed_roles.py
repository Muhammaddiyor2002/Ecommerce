"""Idempotent seeding of system roles."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.users.models import Role

SYSTEM_ROLES = [
    ("customer", "Customer", "End-user shopping on the storefront."),
    ("vendor", "Vendor", "Multi-vendor seller account."),
    ("staff", "Staff", "Internal operations team member."),
    ("admin", "Administrator", "Full administrative access."),
    ("support", "Support", "Customer-support agent."),
]


class Command(BaseCommand):
    help = "Seed system roles (idempotent)."

    def handle(self, *args, **opts):
        for code, name, description in SYSTEM_ROLES:
            obj, created = Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": description, "is_system": True},
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'+' if created else '='} {obj.code}: {obj.name}")
            )
