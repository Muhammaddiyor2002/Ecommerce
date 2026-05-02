"""NovaCommerce Core — FastAPI high-speed service.

Responsibilities:
- High-throughput public read APIs (catalog, search, product detail).
- Async WebSocket endpoints for flash-sale counters, live stock, public events.
- Webhook endpoints that need very low latency (delegating heavy work to
  Celery via Redis).
"""

__version__ = "0.1.0"
