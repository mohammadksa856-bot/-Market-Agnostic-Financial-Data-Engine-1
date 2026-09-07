#!/bin/sh
set -eu

DB_PATH="${FINENGINE_DB_PATH:-/app/data/financial.sqlite3}"
RAW_DIR="${FINENGINE_UNIVERSE_RAW_DIR:-/app/data/raw/universe}"
INTERVAL="${FINENGINE_UNIVERSE_REFRESH_SECONDS:-86400}"

while true; do
    finengine --db "$DB_PATH" universe-sync US --raw-dir "$RAW_DIR"
    # Saudi Exchange serves its directory only after a full browser render. The
    # production image installs Xvfb, allowing Chromium to run in ordinary headed
    # mode without an interactive desktop.
    if command -v xvfb-run >/dev/null 2>&1; then
        xvfb-run -a finengine --db "$DB_PATH" universe-sync SA --raw-dir "$RAW_DIR" --show
    else
        finengine --db "$DB_PATH" universe-sync SA --raw-dir "$RAW_DIR"
    fi
    sleep "$INTERVAL"
done
