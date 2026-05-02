#!/usr/bin/env bash
# =============================================================
# Django container entrypoint
# - waits for postgres + redis
# - runs migrations on the primary worker only
# - collects static
# =============================================================
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${REDIS_URL:?REDIS_URL is required}"

wait_for_tcp() {
    local host="$1" port="$2" name="$3"
    echo ">> waiting for ${name} (${host}:${port})..."
    local timeout=60
    while ! (echo > "/dev/tcp/${host}/${port}") >/dev/null 2>&1; do
        timeout=$((timeout - 1))
        if [ "$timeout" -le 0 ]; then
            echo "!! timed out waiting for ${name}"
            exit 1
        fi
        sleep 1
    done
    echo ">> ${name} is up"
}

PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
RD_HOST="${REDIS_HOST:-redis}"
RD_PORT="${REDIS_PORT:-6379}"

wait_for_tcp "$PG_HOST" "$PG_PORT" "postgres"
wait_for_tcp "$RD_HOST" "$RD_PORT" "redis"

cd /app/django_app

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo ">> running migrations"
    python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-true}" = "true" ]; then
    echo ">> collecting static"
    python manage.py collectstatic --noinput || true
fi

if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo ">> ensuring superuser exists"
    python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
email = '${DJANGO_SUPERUSER_EMAIL}'
if not U.objects.filter(email=email).exists():
    U.objects.create_superuser(email=email, password='${DJANGO_SUPERUSER_PASSWORD}')
    print('superuser created')
else:
    print('superuser exists')
"
fi

echo ">> starting: $*"
exec "$@"
