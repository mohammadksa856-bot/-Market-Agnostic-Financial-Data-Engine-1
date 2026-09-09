#!/bin/sh
set -eu

database="${FINENGINE_DB:-/app/state/financial.sqlite3}"
registry="${FINENGINE_REGISTRY:-/app/config/companies.json}"
interval="${FINENGINE_SUPABASE_SYNC_SECONDS:-300}"

if [ -z "${SUPABASE_URL:-}" ] || { [ -z "${SUPABASE_SECRET_KEY:-}" ] && [ -z "${SUPABASE_SERVICE_KEY:-}" ]; }; then
    echo "SUPABASE_URL and SUPABASE_SECRET_KEY (or legacy SUPABASE_SERVICE_KEY) are required." >&2
    exit 2
fi

while true; do
    if ! finengine --db "$database" export-supabase --all \
        --registry "$registry" --prune; then
        echo "Supabase export failed; retrying after $interval seconds." >&2
    fi
    sleep "$interval"
done
