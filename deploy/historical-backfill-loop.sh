#!/bin/sh
set -u

database="${FINENGINE_DB:-/app/state/financial.sqlite3}"
raw_dir="${FINENGINE_RAW_DIR:-/app/state/raw}"
status_file="${FINENGINE_HISTORICAL_STATUS_FILE:-/app/state/historical-backfill-status.json}"
source_limit="${FINENGINE_HISTORICAL_SOURCE_LIMIT:-500}"
retry_delay="${FINENGINE_HISTORICAL_RETRY_SECONDS:-300}"

mkdir -p "$raw_dir" "$(dirname "$status_file")"

while true; do
    result_file="$(mktemp)"
    error_file="$(mktemp)"
    if finengine --db "$database" sa-historical-backfill \
        --limit 500 --source-limit "$source_limit" --raw-dir "$raw_dir" \
        >"$result_file" 2>"$error_file"; then
        if finengine --db "$database" sa-historical-status >"$status_file.tmp" 2>>"$error_file"; then
            mv "$status_file.tmp" "$status_file"
            rm -f "$result_file" "$error_file"
            sleep "$retry_delay"
            continue
        fi
    fi
    python - "$status_file" "$error_file" <<'PY'
import json, sys
from datetime import datetime, timezone
path, error_path = sys.argv[1:]
try:
    detail = open(error_path, encoding="utf-8").read()[-2000:]
except OSError:
    detail = "historical backfill command failed"
with open(path + ".tmp", "w", encoding="utf-8") as handle:
    json.dump({"status": "failed", "checked_at": datetime.now(timezone.utc).isoformat(),
               "error": detail}, handle, ensure_ascii=False)
    handle.write("\n")
PY
    mv "$status_file.tmp" "$status_file"
    rm -f "$result_file" "$error_file"
    sleep "$retry_delay"
done
