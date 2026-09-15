#!/bin/sh
set -eu

database="${FINENGINE_DB:-/app/state/financial.sqlite3}"
registry="${FINENGINE_REGISTRY:-/app/config/companies.json}"
interval="${FINENGINE_SUPABASE_SYNC_SECONDS:-300}"
status_file="${FINENGINE_SUPABASE_STATUS_FILE:-/tmp/supabase-sync-status.json}"

write_status() {
    state="$1"; detail="$2"
    python - "$status_file" "$state" "$detail" <<'PY'
import json, os, sys, tempfile
from datetime import datetime, timezone

path, state, detail = sys.argv[1:]
directory = os.path.dirname(path) or "."
os.makedirs(directory, exist_ok=True)
fd, temporary = tempfile.mkstemp(prefix=".supabase-status-", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"state": state, "checked_at": datetime.now(timezone.utc).isoformat(),
                   "detail": detail}, handle)
        handle.write("\n")
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
}

if [ -z "${SUPABASE_URL:-}" ] || { [ -z "${SUPABASE_SECRET_KEY:-}" ] && [ -z "${SUPABASE_SERVICE_KEY:-}" ]; }; then
    echo "SUPABASE_URL and SUPABASE_SECRET_KEY (or legacy SUPABASE_SERVICE_KEY) are required." >&2
    exit 2
fi

while true; do
    if finengine --db "$database" export-supabase --all \
        --registry "$registry" --prune; then
        write_status "ready" "latest production snapshot exported"
    else
        write_status "failed" "Supabase export failed; see container logs"
        echo "Supabase export failed; retrying after $interval seconds." >&2
    fi
    sleep "$interval"
done
