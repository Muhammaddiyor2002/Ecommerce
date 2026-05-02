"""Catalog domain — categories, brands, products, variants, attributes, media.

Design notes:
- Trigram indexes on Product.name & Product.description for fast `ilike`/full-text fallback.
- Materialized search_vector keeps full-text fast (populated by triggers/migration data).
- Variants store atomic SKU / pricing / inventory pointer.
- AttributeValues are denormalized JSON on Variant for ultra-fast reads,
  with the relational Attribute/AttributeOption tables for filtering.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedUUIDModel


class Brand(TimeStampedUUIDModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="brands/", null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "catalog_brand"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Category(TimeStampedUUIDModel):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "catalog_category"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Attribute(TimeStampedUUIDModel):
    """A typed attribute (e.g. Color, Size, Material)."""

    class Kind(models.TextChoices):
        TEXT = "text"
        NUMBER = "number"
        BOOLEAN = "boolean"
        OPTION = "option"  # one of predefined AttributeOption rows

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OPTION)
    is_filterable = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)

    class Meta:
        db_table = "catalog_attribute"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AttributeOption(TimeStampedUUIDModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")
    value = models.CharField(max_length=128)
    label = models.CharField(max_length=128)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "catalog_attribute_option"
        unique_together = (("attribute", "value"),)
        ordering = ["sort_order", "label"]

    def __str__(self) -> str:
        return f"{self.attribute.code}={self.value}"


class Product(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft"
        ACTIVE = "active"
        ARCHIVED = "archived"

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)

    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    categories = models.ManyToManyField(Category, related_name="products", blank=True)
    attributes = models.ManyToManyField(Attribute, related_name="products", blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    rating_count = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)

    metadata = models.JSONField(default=dict, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = "catalog_product"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["brand", "status"]),
            GinIndex(fields=["search_vector"], name="catalog_product_sv_gin"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ProductVariant(TimeStampedUUIDModel):
    """An atomic unit of sale (sku-level)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    barcode = models.CharField(max_length=64, blank=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original/strikethrough price for discount display",
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")

    weight_g = models.PositiveIntegerField(default=0, help_text="grams")
    length_mm = models.PositiveIntegerField(default=0)
    width_mm = models.PositiveIntegerField(default=0)
    height_mm = models.PositiveIntegerField(default=0)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    # Denormalized attribute snapshot, e.g. {"color": "red", "size": "M"}
    attributes_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "catalog_product_variant"
        ordering = ["product", "-is_default", "name"]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} :: {self.sku}"

    @property
    def discount_percent(self) -> int:
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(round((1 - (self.price / self.compare_at_price)) * 100))
        return 0


class ProductImage(TimeStampedUUIDModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "catalog_product_image"
        ordering = ["sort_order"]
        indexes = [models.Index(fields=["product", "is_primary"])]
