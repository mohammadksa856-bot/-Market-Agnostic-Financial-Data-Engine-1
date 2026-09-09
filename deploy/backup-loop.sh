#!/bin/sh
set -u

database="${FINENGINE_DB:-/app/state/financial.sqlite3}"
output_dir="${FINENGINE_BACKUP_DIR:-/app/backups}/bundles"
status_file="${FINENGINE_BACKUP_STATUS_FILE:-/app/backups/backup-status.json}"
interval="${FINENGINE_BACKUP_SECONDS:-86400}"
retry_delay="${FINENGINE_BACKUP_RETRY_SECONDS:-900}"
keep="${FINENGINE_BUNDLE_KEEP:-7}"

mkdir -p "$output_dir" "$(dirname "$status_file")"

write_status() {
    state="$1"; detail="$2"; bundle="${3:-}"
    python - "$status_file" "$state" "$detail" "$bundle" <<'PY'
import json, os, sys, tempfile
from datetime import datetime, timezone

path, state, detail, bundle = sys.argv[1:]
payload = {
    "state": state,
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "detail": detail,
    "bundle": bundle or None,
}
directory = os.path.dirname(path) or "."
fd, temporary = tempfile.mkstemp(prefix=".backup-status-", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.write("\n")
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
}

while true; do
    result_file="$(mktemp)"
    if finengine --db "$database" backup-bundle \
        --output-dir "$output_dir" --project-root /app --keep "$keep" >"$result_file" 2>&1; then
        if bundle_path="$(python - "$result_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["bundle"])
PY
        )" && python - "$bundle_path" <<'PY'
import sys
from finengine.operations import verify_portable_bundle
verify_portable_bundle(sys.argv[1])
PY
        then
            write_status "ready" "portable bundle created and independently verified" "$bundle_path"
            rm -f "$result_file"
            sleep "$interval"
            continue
        fi
        detail="bundle verification failed"
    else
        detail="$(tail -n 20 "$result_file" | tr '\n' ' ' | cut -c1-2000)"
    fi
    write_status "failed" "$detail"
    rm -f "$result_file"
    sleep "$retry_delay"
done
