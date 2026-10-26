#!/bin/bash
# Integrate an external coverage snapshot on a third, isolated engine copy. Never touches the original.
# usage: integration_run.sh <original-engine-clone> <external-snapshot.json> <our-bundle.json> <empty-workdir> [extra-imports-dir]
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"; ENGINE="$1"; SNAPSHOT="$2"; OURS="$3"; WORK="$4"; EXTRA="${5:-}"
mkdir -p "$WORK"; [ -z "$(ls -A "$WORK")" ] || { echo "workdir must be empty" >&2; exit 1; }
TOOL="python3 -I $KIT/tools/snapshot_tool.py"
echo "1. structure of the external snapshot"
$TOOL validate "$SNAPSHOT" > "$WORK/1-validate.json" || { cat "$WORK/1-validate.json"; exit 2; }
echo "2. keys, values, periods, definitions and evidence against our bundle"
$TOOL compare "$OURS" "$SNAPSHOT" --out "$WORK/2-compare-ours.json" > "$WORK/2-summary.json"
echo "3. third copy of the engine with the correctness pack"
git clone -q --no-hardlinks "$ENGINE" "$WORK/integration-engine"
( cd "$WORK/integration-engine"
  git fetch -q "$KIT/git/correctness-pack.bundle" "refs/heads/fixes/correctness-pack:fixes/correctness-pack"
  git checkout -q fixes/correctness-pack
  expected="$(git bundle list-heads "$KIT/git/correctness-pack.bundle" | awk '{print $1}')"
  test "$(git rev-parse HEAD)" = "$expected" || { echo "correctness pack is not at $expected" >&2; exit 3; } )
IMPORTS="$WORK/imports"; mkdir -p "$IMPORTS"; cp "$WORK/integration-engine/data/imports/"*.json "$IMPORTS/"
[ -n "$EXTRA" ] && cp "$EXTRA"/*.json "$IMPORTS/"
COMPANY="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['company_id'])" "$SNAPSHOT")"
( cd "$WORK/integration-engine" && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  python3 -m finengine --db "$WORK/integration.sqlite3" bootstrap --imports "$IMPORTS" --registry config/companies.json \
    --raw-dir "$WORK/raw" --html "$WORK/report.html" --csv "$WORK/report.csv" \
    --field-availability-dir config/factory/field-availability > "$WORK/3-bootstrap.log"
  python3 "$KIT/tools/export_from_engine.py" "$WORK/integration.sqlite3" "$COMPANY" "$WORK/integration-bundle.json" \
    "integration@$(git rev-parse --short HEAD)" "$(git rev-parse HEAD)" > "$WORK/3-export.json" )
echo "4. coverage of the union, each contract slot counted once"
$TOOL compare "$WORK/integration-bundle.json" "$SNAPSHOT" --out "$WORK/4-compare-integration.json" > "$WORK/4-summary.json"
echo "5. conflicts that cannot be resolved automatically"
python3 -I "$KIT/tools/escalate.py" "integration=$WORK/4-compare-integration.json" "ours=$WORK/2-compare-ours.json" > "$WORK/5-escalations.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('needs review:',d['needs_review']['count'],'| coverage differences:',d['coverage_differences']['count'])" "$WORK/5-escalations.json"
echo "results in $WORK"
