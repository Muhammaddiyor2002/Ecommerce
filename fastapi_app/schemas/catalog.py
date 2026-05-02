"""Pydantic schemas for FastAPI catalog endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BrandOut(_Base):
    id: UUID
    name: str
    slug: str
    is_active: bool


class CategoryOut(_Base):
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None = None
    is_active: bool
    sort_order: int


class VariantOut(_Base):
    id: UUID
    sku: str
    name: str | None = None
    price: Decimal
    compare_at_price: Decimal | None = None
    currency: str
    is_default: bool
    is_active: bool
    attributes_snapshot: dict = {}
    product_id: UUID | None = None
    product_slug: str | None = None
    product_name: str | None = None


class ProductImageOut(_Base):
    id: UUID
    image: str
    alt_text: str | None = ""
    sort_order: int = 0
    is_primary: bool = False
    variant_id: UUID | None = None


class ProductOut(_Base):
    id: UUID
    name: str
    slug: str
    short_description: str | None = ""
    brand_id: UUID | None = None
    status: str
    is_featured: bool = False
    rating_avg: Decimal | None = None
    rating_count: int = 0
    sold_count: int = 0
    created_at: datetime
    min_price: Decimal | None = None
    primary_image: str | None = None


class ProductDetailOut(ProductOut):
    description: str | None = ""
    metadata: dict = {}
    brand_name: str | None = None
    brand_slug: str | None = None
    variants: list[VariantOut] = []
    images: list[ProductImageOut] = []


class PaginatedProducts(_Base):
    items: list[ProductOut]
    next_cursor: str | None = None
    page_size: int
