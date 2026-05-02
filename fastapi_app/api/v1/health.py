from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_session
from ...core.redis import get_cache

router = APIRouter()
_started_at = time.monotonic()


@router.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok", "uptime_s": round(time.monotonic() - _started_at, 2)}


@router.get("/readyz", include_in_schema=False)
async def readyz(session: AsyncSession = Depends(get_session)):
    """Verifies DB and Redis are reachable; used by Kubernetes readiness probes."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        return {"ready": False, "db_error": str(exc)}, 503
    try:
        cache = await get_cache()
        await cache.ping()
    except Exception as exc:  # pragma: no cover
        return {"ready": False, "redis_error": str(exc)}, 503
    return {"ready": True}
