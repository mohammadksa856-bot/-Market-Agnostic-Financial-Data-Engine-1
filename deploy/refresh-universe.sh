#!/bin/sh
set -eu

DB_PATH="${FINENGINE_DB_PATH:-/app/data/financial.sqlite3}"
RAW_DIR="${FINENGINE_UNIVERSE_RAW_DIR:-/app/data/raw/universe}"
INTERVAL="${FINENGINE_UNIVERSE_REFRESH_SECONDS:-86400}"

while true; do
    finengine --db "$DB_PATH" universe-sync US --raw-dir "$RAW_DIR"
    finengine --db "$DB_PATH" universe-sync SA --raw-dir "$RAW_DIR"
    sleep "$INTERVAL"
done
