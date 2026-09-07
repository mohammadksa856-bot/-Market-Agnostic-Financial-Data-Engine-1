#!/bin/sh
set -eu

database="${FINENGINE_DB:-/app/data/financial.sqlite3}"
interval="${FINENGINE_SCHEDULE_SECONDS:-21600}"
source_limit="${FINENGINE_SOURCE_LIMIT:-50}"

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

# Idempotent upserts: restarting the container never duplicates schedules and
# preserves each schedule's next-run cursor.
finengine --db "$database" configure-production --every "$interval" --source-limit "$source_limit"

if [ "${FINENGINE_BROWSER_HEADLESS:-false}" = "false" ] && command -v xvfb-run >/dev/null 2>&1; then
    exec xvfb-run -a finengine --db "$database" run --host 0.0.0.0 --port 8000 --poll 10
fi
exec finengine --db "$database" run --host 0.0.0.0 --port 8000 --poll 10
