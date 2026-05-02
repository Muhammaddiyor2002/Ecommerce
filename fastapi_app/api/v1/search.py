"""Search & autocomplete (Postgres ts_vector + trigram fallback).

Drop-in replaceable with Elasticsearch / Meilisearch later — the response
shape is identical.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_session

router = APIRouter()


@router.get("")
async def search(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    session: AsyncSession = Depends(get_session),
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
):
    rows = (
        await session.execute(
            text("""
        SELECT
            p.id, p.name, p.slug, p.short_description,
            (SELECT MIN(v.price) FROM catalog_product_variant v
              WHERE v.product_id = p.id AND v.is_active = true) AS min_price,
            ts_rank(
                COALESCE(p.search_vector, to_tsvector('simple', p.name || ' ' || COALESCE(p.short_description, ''))),
                websearch_to_tsquery('simple', :q)
            ) AS rank,
            similarity(p.name, :q) AS sim
        FROM catalog_product p
        WHERE p.status = 'active' AND p.deleted_at IS NULL
          AND (
            COALESCE(p.search_vector, to_tsvector('simple', p.name || ' ' || COALESCE(p.short_description, ''))) @@ websearch_to_tsquery('simple', :q)
            OR p.name % :q
          )
        ORDER BY rank DESC, sim DESC NULLS LAST, p.sold_count DESC
        LIMIT :limit
    """),
            {"q": q, "limit": page_size},
        )
    ).fetchall()
    return {
        "query": q,
        "items": [dict(r._mapping) for r in rows],
    }


@router.get("/autocomplete")
async def autocomplete(
    q: Annotated[str, Query(min_length=1, max_length=80)],
    session: AsyncSession = Depends(get_session),
):
    rows = (
        await session.execute(
            text("""
        SELECT name, slug
        FROM catalog_product
        WHERE status = 'active' AND deleted_at IS NULL AND name ILIKE :q
        ORDER BY sold_count DESC, name
        LIMIT 10
    """),
            {"q": f"{q}%"},
        )
    ).fetchall()
    return [dict(r._mapping) for r in rows]
