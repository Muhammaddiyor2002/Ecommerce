# NovaCommerce Core

**Production-grade e-commerce backend platform — Django + FastAPI hybrid.**

NovaCommerce Core is built to power high-traffic online storefronts, mobile
apps, admin panels, and 3rd-party integrations. It is engineered from the
ground up for **horizontal scaling, real-time updates, and enterprise
reliability**.

[![CI](https://github.com/Muhammaddiyor2002/NovaCommerce-Core/actions/workflows/ci.yml/badge.svg)](https://github.com/Muhammaddiyor2002/NovaCommerce-Core/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Muhammaddiyor2002/NovaCommerce-Core/actions/workflows/codeql.yml/badge.svg)](https://github.com/Muhammaddiyor2002/NovaCommerce-Core/actions/workflows/codeql.yml)
![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-teal)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Architecture

```
                       ┌─────────────────────────┐
                       │       Nginx / LB        │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┴──────────────────────┐
            │                                              │
   ┌────────▼────────┐                            ┌────────▼─────────┐
   │   Django + DRF   │                            │     FastAPI      │
   │  (admin, auth,   │                            │ (high-speed read │
   │   orders, pay,   │                            │   APIs, search,  │
   │   business core) │                            │  websockets)     │
   └────────┬─────────┘                            └────────┬─────────┘
            │                                              │
            │     ┌────────────────────────────────┐       │
            └─────► PostgreSQL (primary + replica) ◄───────┘
                  └────────────────┬───────────────┘
                                   │
            ┌──────────────────────┴────────────────────────┐
            │                                                │
     ┌──────▼──────┐                                  ┌──────▼──────┐
     │    Redis    │                                  │   Celery    │
     │ cache + ws  │                                  │  workers    │
     └─────────────┘                                  └─────────────┘
```

* **Django** owns ACID-heavy paths (auth, orders, payments, admin, audit).
* **FastAPI** owns high-RPS read paths (catalog, search, websockets, webhooks).
* Both share the **same PostgreSQL schema** & validate the **same JWT**.
* **Channels + Daphne** power authenticated WebSockets for live order updates.
* **Celery** handles email, payment captures, analytics rollups, snapshots.
* **Redis** is the single Swiss-army knife: cache, session, queue, channels, pub/sub.

---

## Module map

```
django_app/
├── novacommerce/              # project-level settings (base/dev/prod/test)
└── apps/
    ├── core/                  # request-id middleware, base models, db router
    ├── users/                 # custom User, Roles (RBAC), Addresses, Wishlist
    ├── catalog/               # Brand, Category, Product, Variant, Image, Attribute
    ├── inventory/             # Warehouse, Stock, StockMovement (atomic reservations)
    ├── cart/                  # Cart, CartItem, anonymous→user merge on login
    ├── coupons/               # Percent / Fixed / FreeShipping coupons
    ├── checkout/              # entrypoint endpoints
    ├── orders/                # Order, OrderItem, OrderEvent, status state machine
    ├── payments/              # multi-provider (Stripe/PayPal/Click/Payme/Uzum/Manual)
    ├── shipping/              # ShippingMethod, Shipment, tracking
    ├── reviews/               # Review + moderation
    ├── notifications/         # Email/SMS/Push fan-out
    ├── analytics/             # daily snapshots + admin dashboard endpoint
    ├── audit/                 # AuditLog + AuditTrail middleware
    └── realtime/              # Channels consumers (order, user, admin firehose)

fastapi_app/
├── core/                      # config, db, redis, security, logging
├── api/v1/
│   ├── catalog.py             # /products, /categories, /brands, /variants
│   ├── search.py              # full-text search + autocomplete
│   ├── realtime.py            # websocket flash-sale, live stock counter
│   ├── webhooks.py            # async webhook intake
│   └── health.py              # /healthz + /readyz
└── realtime/manager.py        # Redis-backed pub/sub WebSocket fanout

k8s/                           # Kubernetes manifests (deployments, HPAs, ingress)
docker/                        # Multi-stage Dockerfiles + entrypoints + nginx config
.github/workflows/             # CI (lint+tests+build) + CodeQL
scripts/                       # backup.sh, restore.sh, init_db.sql
tests/                         # pytest suite (unit, API, security, concurrency)
```

---

## Local setup (dev, ~3 minutes)

### Prereqs
* Python 3.13+
* PostgreSQL 16 (or just use docker compose)
* Redis 7
* Docker (recommended)

### Option A — Docker compose (fastest)

```bash
cp .env.example .env

docker compose up -d --build           # build + run all services
docker compose exec django ./manage.py migrate
docker compose exec django ./manage.py seed_roles
docker compose exec django ./manage.py seed_demo
docker compose exec django ./manage.py createsuperuser
```

Services:

| Component   | URL                                      |
| ----------- | ---------------------------------------- |
| Django API  | http://localhost:8000/api/v1/            |
| FastAPI     | http://localhost:8001/api/v1/            |
| Admin       | http://localhost:8000/admin/             |
| OpenAPI doc | http://localhost:8000/api/v1/docs/       |
| FastAPI doc | http://localhost:8001/docs               |
| Postgres    | localhost:5432 (`novacommerce` db)       |
| Redis       | localhost:6379                           |

### Option B — Local virtualenv

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt

# Django
export DJANGO_SETTINGS_MODULE=novacommerce.settings.dev
export PYTHONPATH=$PWD/django_app
python django_app/manage.py migrate
python django_app/manage.py runserver 0.0.0.0:8000

# FastAPI (separate shell)
uvicorn fastapi_app.main:app --reload --port 8001
```

---

## Running the test suite

```bash
DJANGO_SETTINGS_MODULE=novacommerce.settings.test \
PYTHONPATH=django_app \
pytest -ra --cov --cov-report=term-missing
```

Test types in `tests/`:

* `test_auth.py` — register, login, refresh, JWT-protected endpoints
* `test_cart.py` — add/update/remove, oversell rejection (HTTP 409)
* `test_inventory.py` — atomic reserve / release / commit
* `test_orders.py` — checkout flow, status transitions, cancel-releases-stock
* `test_coupons.py` — percent, fixed, capping, min-subtotal
* `test_payments.py` — provider lookup, charge creation, JSON-safe storage
* `test_concurrency.py` — repeated-call exhaustion semantics
* `test_security.py` — cross-tenant access denial, anonymous rejection
* `test_health.py` — `/healthz` smoke

The CI workflow (`ci.yml`) runs lint + tests on every PR.

---

## Production deployment

### Docker (single-host)

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This boots Django (gunicorn-uvicorn workers), FastAPI (uvicorn), Celery
worker + beat, Postgres, Redis, and Nginx as TLS terminator.

### Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl create secret generic novacommerce-secrets \
    --from-env-file=.env --namespace=novacommerce
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/django-deployment.yaml
kubectl apply -f k8s/fastapi-deployment.yaml
kubectl apply -f k8s/celery-worker.yaml
kubectl apply -f k8s/ingress.yaml
```

The HPAs scale Django 4→30 pods and FastAPI 6→60 pods on CPU.
Replace the secret example with **External Secrets Operator** or **Sealed
Secrets** in production.

### Database backups

```bash
./scripts/backup.sh                                  # pg_dump → S3
./scripts/restore.sh backups/2025-05-02.dump.gz      # restore from a dump
```

---

## Security

* Custom User model with **email login** + RBAC (Role × User M2M).
* **JWT** (SimpleJWT) — short-lived access tokens (15 min) + 14-day refresh tokens with rotation + blacklist.
* **CSRF** + clickjacking + secure-cookies + HSTS in `settings.prod`.
* **Rate-limiting** via DRF throttles (`anon`, `user`, sensitive `auth` scope).
* **Webhooks** verified per-provider (Stripe sig header, Click MD5 sign, Payme Basic auth).
* **Audit trail** on all `POST/PUT/PATCH/DELETE` on `/admin/` & `/api/admin/`.
* **CodeQL** scans on every PR.
* **Dependabot** weekly bumps for pip, GitHub Actions, Docker.
* **OWASP** alignment: input validation everywhere via DRF/Pydantic, parameterised queries via ORM, no shell interpolation.

---

## Real-time

WebSockets terminated by Daphne (Django Channels) and FastAPI both:

* `ws://…/ws/orders/<order_id>/` — order status updates (owner or staff only)
* `ws://…/ws/me/` — authenticated user firehose
* `ws://…/ws/admin/dashboard/` — staff metrics
* `ws://…/api/v1/realtime/ws/flash-sale/<sale_id>/` (FastAPI) — flash sale counter
* `ws://…/api/v1/realtime/ws/stock/<sku>/` — live stock for a SKU

Pub/sub backplane is Redis (`channels_redis` for Django, `aioredis` for FastAPI).

---

## Performance

* **Connection pooling** via `CONN_MAX_AGE=300` and pgbouncer-friendly settings.
* **Read replica** routing through `apps.core.db_router.PrimaryReplicaRouter`.
* **Cursor pagination** on hot list endpoints.
* **Cache layers**: per-view (DRF), per-call (Redis) for catalog, materialised search vectors.
* **Atomic stock ops** with `select_for_update()` to prevent oversells.
* **Async I/O** in FastAPI via `asyncpg` + `redis.asyncio`.
* **Horizontal scaling**: stateless app pods + Redis-backed Channels group.

Target: **200K+ concurrent connections, sub-200ms common reads** with sufficient pods + RDS.

---

## API documentation

* DRF: `/api/v1/docs/` (Swagger UI), `/api/v1/redoc/`, `/api/v1/schema/` (OpenAPI 3 JSON)
* FastAPI: `/docs`, `/redoc`

---

## License

MIT — see [LICENSE](LICENSE).
