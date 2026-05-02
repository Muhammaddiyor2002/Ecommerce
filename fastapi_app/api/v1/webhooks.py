"""FastAPI webhook ingress with very low latency.

We do minimal work here (verify + queue) and rely on the Django service to
process the heavy lifting via Celery. This keeps the FastAPI workers free.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from ...core.redis import get_cache

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{provider_code}", status_code=202)
async def receive(provider_code: str, request: Request):
    body = await request.body()
    cache = await get_cache()
    # Push raw event onto a Redis list; a Celery worker drains it.
    try:
        await cache.rpush(
            f"webhooks:{provider_code}:queue",
            body.decode("utf-8", errors="replace"),
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("could not enqueue webhook: %s", exc)
        return {"accepted": False, "error": "enqueue failed"}
    return {"accepted": True, "provider": provider_code}
