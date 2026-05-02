"""FastAPI service entrypoint.

Includes:
- /healthz, /readyz             liveness/readiness probes
- /api/v1/catalog/*             public read APIs (categories, products)
- /api/v1/search/*              full-text + faceted search
- /api/v1/realtime/*            WebSocket endpoints (flash sales, stock)
- /api/v1/webhooks/*            very-low-latency webhook ingress
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from .api.v1 import catalog, health, realtime, search, webhooks
from .core.config import get_settings
from .core.logging import configure_logging
from .core.redis import close_redis

logger = logging.getLogger("novacommerce.fastapi")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("fastapi starting", extra={"env": settings.env})
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.env)
        except ImportError:  # pragma: no cover
            logger.warning("sentry-sdk not installed")
    yield
    await close_redis()
    logger.info("fastapi shutting down")


app = FastAPI(
    title="NovaCommerce Core — FastAPI",
    version="1.0.0",
    description="High-speed public APIs for the NovaCommerce platform.",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "novacommerce-fastapi", "version": app.version}
