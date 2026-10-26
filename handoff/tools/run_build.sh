#!/bin/bash
# Isolated full build and SABIC readiness, from the repository root.
# usage: handoff/tools/run_build.sh <run-name> [field-availability-dir]
# Output: runs/<run-name>/{db.sqlite3,bootstrap.log,ready-2010.json}. Unsigned drafts are never in the default dir.
set -e
N=${1:?run name}; FA=${2:-handoff/field-availability/conclusive-candidates}
OUT=${RUNS_DIR:-runs}/$N; mkdir -p "$OUT"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m finengine --db "$OUT/db.sqlite3" bootstrap \
  --imports data/imports --registry config/companies.json --raw-dir "$OUT/raw" \
  --html "$OUT/r.html" --csv "$OUT/r.csv" --field-availability-dir "$FA" > "$OUT/bootstrap.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m finengine --db "$OUT/db.sqlite3" \
  factory-contract-readiness SA 2010 > "$OUT/ready-2010.json"
python3 -c "import json,sys; d=json.load(open('$OUT/ready-2010.json')); print('$N', d['total_score'][:7], len(d['blocking_reasons']), 'blocking')"
