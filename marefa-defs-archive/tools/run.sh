#!/bin/bash
# usage: run.sh <engine_dir> <imports_dir> <name>
W=/tmp/claude-0/-home-user/f6c8e9e6-4cc9-5437-a0b5-9dc9df4ba352/scratchpad/defs; R=/home/user/mohammadksa856-bot/-market-agnostic-financial-data-engine-1
E=$1; I=$2; N=$3; mkdir -p $W/runs/$N; cd $E
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m finengine --db $W/runs/$N/db.sqlite3 bootstrap --imports $I --registry $R/config/companies.json --raw-dir $W/runs/$N/raw --html $W/runs/$N/r.html --csv $W/runs/$N/r.csv --field-availability-dir $R/config/factory/field-availability > $W/runs/$N/bootstrap.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m finengine --db $W/runs/$N/db.sqlite3 factory-contract-readiness SA 2222 > $W/runs/$N/ready.json 2>&1
echo "$N done $?"
