#!/usr/bin/env bash
# Minimal wait-for-it (tcp port wait).
# Usage: wait-for-it.sh host:port -- cmd args...
set -e
HOSTPORT="${1:?host:port required}"; shift
HOST="${HOSTPORT%%:*}"
PORT="${HOSTPORT##*:}"
TIMEOUT="${WAIT_TIMEOUT:-60}"

echo ">> waiting for ${HOST}:${PORT} (timeout ${TIMEOUT}s)..."
while ! (echo > "/dev/tcp/${HOST}/${PORT}") >/dev/null 2>&1; do
    TIMEOUT=$((TIMEOUT - 1))
    [ "$TIMEOUT" -le 0 ] && { echo "!! timed out"; exit 1; }
    sleep 1
done
echo ">> ${HOST}:${PORT} is up"

[ "${1:-}" = "--" ] && shift
exec "$@"
