#!/bin/sh
set -eu

state_dir="${FINENGINE_STATE_DIR:-/app/state}"
database="${FINENGINE_DB:-$state_dir/financial.sqlite3}"
raw_dir="${FINENGINE_RAW_DIR:-$state_dir/raw}"
interval="${FINENGINE_SCHEDULE_SECONDS:-21600}"
source_limit="${FINENGINE_SOURCE_LIMIT:-50}"
registry="${FINENGINE_REGISTRY:-/app/config/companies.json}"
imports="${FINENGINE_IMPORTS:-/app/data/imports}"
seed_raw="${FINENGINE_SEED_RAW_DIR:-/app/data/raw}"

case "${SEC_USER_AGENT:-}" in
  ""|*"operator@example.com"*)
    echo "SEC_USER_AGENT must identify the real operator and monitored email address." >&2
    exit 2
    ;;
  *"@"*) ;;
  *)
    echo "SEC_USER_AGENT must include a monitored email address." >&2
    exit 2
    ;;
esac

mkdir -p "$state_dir" "$raw_dir"

# A fresh persistent volume starts from the reviewed, reproducible manifests
# baked into the image. Existing state is never replaced during a deployment.
if [ ! -s "$database" ]; then
    finengine --db "$database" bootstrap \
        --imports "$imports" --registry "$registry" --raw-dir "$seed_raw" --replace
fi

# Idempotent upserts: restarting the container never duplicates schedules and
# preserves each schedule's next-run cursor.
finengine --db "$database" configure-production --registry "$registry" \
    --raw-dir "$raw_dir" --every "$interval" --source-limit "$source_limit"

if [ "${FINENGINE_BROWSER_HEADLESS:-false}" = "false" ] && command -v xvfb-run >/dev/null 2>&1; then
    exec xvfb-run -a finengine --db "$database" run --host 0.0.0.0 --port 8000 --poll 10
fi
exec finengine --db "$database" run --host 0.0.0.0 --port 8000 --poll 10
