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

exec finengine --db "$database" run --host 0.0.0.0 --port 8000 --poll 10
