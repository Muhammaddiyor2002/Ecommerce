"""Seed demo catalog data for local dev / smoke tests."""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.inventory.models import Stock, Warehouse


class Command(BaseCommand):
    help = "Seed demo catalog data (brands, categories, products, variants, stocks)."

    @transaction.atomic
    def handle(self, *args, **opts):
        warehouse, _ = Warehouse.objects.get_or_create(
            code="main",
            defaults={"name": "Main warehouse", "is_active": True},
        )

        for slug, name in [("apparel", "Apparel"), ("electronics", "Electronics")]:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})

        for slug, name in [("nova", "Nova"), ("acme", "ACME")]:
            Brand.objects.get_or_create(slug=slug, defaults={"name": name})

        nova = Brand.objects.get(slug="nova")
        apparel = Category.objects.get(slug="apparel")
        electronics = Category.objects.get(slug="electronics")

        product, _ = Product.objects.get_or_create(
            slug="nova-tee",
            defaults={
                "name": "Nova Classic Tee",
                "brand": nova,
                "short_description": "Soft cotton tee",
                "description": "A clean, soft-cotton tee from Nova.",
                "status": Product.Status.ACTIVE,
                "is_featured": True,
            },
        )
        product.categories.add(apparel)

        for size, price in [
            ("S", Decimal("19.99")),
            ("M", Decimal("19.99")),
            ("L", Decimal("21.99")),
        ]:
            v, _ = ProductVariant.objects.get_or_create(
                sku=f"NOVA-TEE-{size}",
                defaults={
                    "product": product,
                    "name": f"Size {size}",
                    "price": price,
                    "compare_at_price": Decimal("24.99"),
                    "is_default": size == "M",
                    "is_active": True,
                    "attributes_snapshot": {"size": size, "color": "black"},
                },
            )
            stock, _ = Stock.objects.get_or_create(variant=v, warehouse=warehouse)
            if stock.on_hand < 100:
                stock.on_hand = 100
                stock.save(update_fields=["on_hand"])

        product2, _ = Product.objects.get_or_create(
            slug="nova-headphones",
            defaults={
                "name": "Nova Wireless Headphones",
                "brand": nova,
                "short_description": "ANC over-ear headphones",
                "description": "Premium noise-cancelling headphones with 40h battery.",
                "status": Product.Status.ACTIVE,
                "is_featured": True,
            },
        )
        product2.categories.add(electronics)
        v2, _ = ProductVariant.objects.get_or_create(
            sku="NOVA-HP-BLK",
            defaults={
                "product": product2,
                "name": "Black",
                "price": Decimal("199.00"),
                "compare_at_price": Decimal("249.00"),
                "is_default": True,
                "is_active": True,
                "attributes_snapshot": {"color": "black"},
            },
        )
        Stock.objects.get_or_create(variant=v2, warehouse=warehouse, defaults={"on_hand": 50})

        self.stdout.write(self.style.SUCCESS("demo catalog seeded"))
