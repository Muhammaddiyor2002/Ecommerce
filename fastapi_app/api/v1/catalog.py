"""High-throughput catalog read endpoints.

Implementation notes:
- All queries hit the read replica when configured (see settings.async_database_url).
- Aggressive Redis caching with stale-while-revalidate semantics.
- Cursor pagination by created_at to keep deep pages fast.
"""

from __future__ import annotations

from typing import Annotated

import orjson
from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_session
from ...core.redis import get_cache
from ...schemas.catalog import (
    BrandOut,
    CategoryOut,
    PaginatedProducts,
    ProductDetailOut,
    VariantOut,
)

router = APIRouter()
CACHE_TTL_SHORT = 30
CACHE_TTL_LONG = 300


# ---------- helpers ----------
def _row_to_dict(row) -> dict:
    return dict(row._mapping)


async def _cache_get(cache: Redis, key: str):
    try:
        raw = await cache.get(key)
        if raw:
            return orjson.loads(raw)
    except Exception:
        return None
    return None


async def _cache_set(cache: Redis, key: str, value, ttl: int):
    try:
        await cache.set(key, orjson.dumps(value), ex=ttl)
    except Exception:
        pass


# ---------- endpoints ----------
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
    parent_slug: str | None = None,
):
    cache_key = f"catalog:categories:{parent_slug or 'root'}"
    if cached := await _cache_get(cache, cache_key):
        return cached

    if parent_slug:
        sql = text("""
            SELECT c.id, c.name, c.slug, c.parent_id, c.is_active, c.sort_order
            FROM catalog_category c
            JOIN catalog_category p ON p.id = c.parent_id
            WHERE c.is_active = true AND p.slug = :slug
            ORDER BY c.sort_order, c.name
        """)
        rows = (await session.execute(sql, {"slug": parent_slug})).fetchall()
    else:
        sql = text("""
            SELECT id, name, slug, parent_id, is_active, sort_order
            FROM catalog_category
            WHERE is_active = true AND parent_id IS NULL
            ORDER BY sort_order, name
        """)
        rows = (await session.execute(sql)).fetchall()
    out = [_row_to_dict(r) for r in rows]
    await _cache_set(cache, cache_key, out, CACHE_TTL_LONG)
    return out


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
):
    cache_key = "catalog:brands"
    if cached := await _cache_get(cache, cache_key):
        return cached
    rows = (
        await session.execute(
            text("""
        SELECT id, name, slug, is_active
        FROM catalog_brand
        WHERE is_active = true
        ORDER BY name
    """)
        )
    ).fetchall()
    out = [_row_to_dict(r) for r in rows]
    await _cache_set(cache, cache_key, out, CACHE_TTL_LONG)
    return out


@router.get("/products", response_model=PaginatedProducts)
async def list_products(
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    cursor: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query(description="category slug")] = None,
    brand: Annotated[str | None, Query(description="brand slug")] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    sort: Annotated[str, Query(pattern="^(newest|price_asc|price_desc|popular)$")] = "newest",
):
    where = ["p.status = 'active' AND p.deleted_at IS NULL"]
    params: dict = {"limit": page_size + 1}

    if category:
        where.append(
            "EXISTS (SELECT 1 FROM catalog_product_categories pc "
            "JOIN catalog_category c ON c.id = pc.category_id "
            "WHERE pc.product_id = p.id AND c.slug = :cat)"
        )
        params["cat"] = category
    if brand:
        where.append("p.brand_id = (SELECT id FROM catalog_brand WHERE slug = :brand LIMIT 1)")
        params["brand"] = brand
    if min_price is not None:
        where.append(
            "EXISTS (SELECT 1 FROM catalog_product_variant v "
            "WHERE v.product_id = p.id AND v.is_active = true AND v.price >= :min_price)"
        )
        params["min_price"] = min_price
    if max_price is not None:
        where.append(
            "EXISTS (SELECT 1 FROM catalog_product_variant v "
            "WHERE v.product_id = p.id AND v.is_active = true AND v.price <= :max_price)"
        )
        params["max_price"] = max_price

    if cursor:
        where.append("p.created_at < :cursor")
        params["cursor"] = cursor

    order = {
        "newest": "p.created_at DESC",
        "popular": "p.sold_count DESC, p.created_at DESC",
        "price_asc": "min_price ASC NULLS LAST, p.created_at DESC",
        "price_desc": "min_price DESC NULLS LAST, p.created_at DESC",
    }[sort]

    where_sql = " AND ".join(where)
    sql = text(f"""
        SELECT
            p.id, p.name, p.slug, p.short_description, p.brand_id, p.status,
            p.is_featured, p.rating_avg, p.rating_count, p.sold_count, p.created_at,
            (SELECT MIN(v.price) FROM catalog_product_variant v
              WHERE v.product_id = p.id AND v.is_active = true) AS min_price,
            (SELECT image FROM catalog_product_image i
              WHERE i.product_id = p.id ORDER BY i.is_primary DESC, i.sort_order LIMIT 1) AS primary_image
        FROM catalog_product p
        WHERE {where_sql}
        ORDER BY {order}
        LIMIT :limit
    """)
    rows = (await session.execute(sql, params)).fetchall()
    items = [_row_to_dict(r) for r in rows]
    has_more = len(items) > page_size
    if has_more:
        items = items[:page_size]
    next_cursor = items[-1]["created_at"].isoformat() if has_more and items else None
    return {"items": items, "next_cursor": next_cursor, "page_size": page_size}


@router.get("/products/{slug}", response_model=ProductDetailOut)
async def product_detail(
    slug: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
):
    cache_key = f"catalog:product:{slug}"
    if cached := await _cache_get(cache, cache_key):
        return cached

    row = (
        await session.execute(
            text("""
        SELECT p.id, p.name, p.slug, p.short_description, p.description,
               p.brand_id, p.status, p.is_featured,
               p.rating_avg, p.rating_count, p.sold_count,
               p.metadata, p.created_at,
               b.name AS brand_name, b.slug AS brand_slug
        FROM catalog_product p
        LEFT JOIN catalog_brand b ON b.id = p.brand_id
        WHERE p.slug = :slug AND p.status = 'active' AND p.deleted_at IS NULL
        LIMIT 1
    """),
            {"slug": slug},
        )
    ).first()
    if row is None:
        raise HTTPException(404, "product not found")
    product = _row_to_dict(row)

    variants = [
        _row_to_dict(r)
        for r in (
            await session.execute(
                text("""
            SELECT id, sku, name, price, compare_at_price, currency,
                   is_default, is_active, attributes_snapshot
            FROM catalog_product_variant
            WHERE product_id = :pid AND is_active = true
            ORDER BY is_default DESC, name
        """),
                {"pid": product["id"]},
            )
        ).fetchall()
    ]
    images = [
        _row_to_dict(r)
        for r in (
            await session.execute(
                text("""
            SELECT id, image, alt_text, sort_order, is_primary, variant_id
            FROM catalog_product_image
            WHERE product_id = :pid
            ORDER BY is_primary DESC, sort_order
        """),
                {"pid": product["id"]},
            )
        ).fetchall()
    ]
    out = {**product, "variants": variants, "images": images}
    await _cache_set(cache, cache_key, out, CACHE_TTL_SHORT)
    return out


@router.get("/variants/{sku}", response_model=VariantOut)
async def variant_by_sku(
    sku: str,
    session: AsyncSession = Depends(get_session),
):
    row = (
        await session.execute(
            text("""
        SELECT v.id, v.sku, v.name, v.price, v.compare_at_price, v.currency,
               v.is_default, v.is_active, v.attributes_snapshot,
               v.product_id, p.slug AS product_slug, p.name AS product_name
        FROM catalog_product_variant v
        JOIN catalog_product p ON p.id = v.product_id
        WHERE v.sku = :sku AND v.is_active = true
    """),
            {"sku": sku},
        )
    ).first()
    if row is None:
        raise HTTPException(404, "variant not found")
    return _row_to_dict(row)
