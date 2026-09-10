#!/bin/sh
set -u

database="${FINENGINE_DB:-/app/state/financial.sqlite3}"
raw_dir="${FINENGINE_ONBOARDING_RAW_DIR:-/app/state/raw/universe}"
status_file="${FINENGINE_ONBOARDING_STATUS_FILE:-/app/state/onboarding-status.json}"
interval="${FINENGINE_ONBOARDING_SECONDS:-86400}"
retry_delay="${FINENGINE_ONBOARDING_RETRY_SECONDS:-900}"
us_limit="${FINENGINE_ONBOARDING_US_LIMIT:-25}"
sa_limit="${FINENGINE_ONBOARDING_SA_LIMIT:-10}"
schedule_every="${FINENGINE_ONBOARDING_SCHEDULE_SECONDS:-86400}"

mkdir -p "$raw_dir" "$(dirname "$status_file")"

write_status() {
    state="$1"; detail="$2"; result="${3:-}"
    python - "$status_file" "$state" "$detail" "$result" <<'PY'
import json, os, sys, tempfile
from datetime import datetime, timezone
path, state, detail, result = sys.argv[1:]
payload = {"state": state, "checked_at": datetime.now(timezone.utc).isoformat(),
           "detail": detail, "result": json.loads(result) if result else None}
fd, temporary = tempfile.mkstemp(prefix=".onboarding-status-", dir=os.path.dirname(path) or ".")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False); handle.write("\n")
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary): os.unlink(temporary)
PY
}

while true; do
    result_file="$(mktemp)"; error_file="$(mktemp)"
    if finengine --db "$database" universe-onboard --raw-dir "$raw_dir" \
        --us-limit "$us_limit" --sa-limit "$sa_limit" \
        --schedule-every "$schedule_every" >"$result_file" 2>"$error_file"; then
        result="$(cat "$result_file")"
        write_status "ready" "bounded onboarding cycle completed" "$result"
        rm -f "$result_file" "$error_file"
        sleep "$interval"
        continue
    fi
    detail="$(tail -n 20 "$error_file" | tr '\n' ' ' | cut -c1-2000)"
    write_status "failed" "$detail"
    rm -f "$result_file" "$error_file"
    sleep "$retry_delay"
done
