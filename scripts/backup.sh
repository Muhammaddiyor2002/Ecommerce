#!/usr/bin/env bash
# =============================================================
# NovaCommerce Core — Postgres backup
# Usage: ./scripts/backup.sh [output_dir]
# Creates a timestamped pg_dump in custom format.
# =============================================================
set -euo pipefail

OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"

: "${POSTGRES_HOST:?POSTGRES_HOST required}"
: "${POSTGRES_USER:?POSTGRES_USER required}"
: "${POSTGRES_DB:?POSTGRES_DB required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}"

TS="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="${OUT_DIR}/novacommerce-${TS}.dump"

echo ">> dumping ${POSTGRES_DB} -> ${OUT_FILE}"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    --host="$POSTGRES_HOST" \
    --port="${POSTGRES_PORT:-5432}" \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --format=custom \
    --compress=6 \
    --jobs=4 \
    --no-owner \
    --no-privileges \
    --file="$OUT_FILE.tmp"

mv "$OUT_FILE.tmp" "$OUT_FILE"
echo ">> backup OK: $(du -h "$OUT_FILE" | cut -f1)"

# Optional S3 upload
if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
    aws s3 cp "$OUT_FILE" "s3://${BACKUP_S3_BUCKET}/novacommerce/${TS}.dump"
    echo ">> uploaded to s3://${BACKUP_S3_BUCKET}/novacommerce/${TS}.dump"
fi

# Retain last 14 days locally
find "$OUT_DIR" -name "novacommerce-*.dump" -mtime +14 -delete || true
