#!/usr/bin/env bash
# =============================================================
# NovaCommerce Core — Postgres restore
# Usage: ./scripts/restore.sh path/to/dump-file
# =============================================================
set -euo pipefail

DUMP="${1:?usage: $0 <dump-file>}"
[ -f "$DUMP" ] || { echo "!! file not found: $DUMP"; exit 1; }

: "${POSTGRES_HOST:?POSTGRES_HOST required}"
: "${POSTGRES_USER:?POSTGRES_USER required}"
: "${POSTGRES_DB:?POSTGRES_DB required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}"

echo ">> restoring $DUMP into $POSTGRES_DB"
PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
    --host="$POSTGRES_HOST" \
    --port="${POSTGRES_PORT:-5432}" \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --jobs=4 \
    "$DUMP"
echo ">> restore done"
