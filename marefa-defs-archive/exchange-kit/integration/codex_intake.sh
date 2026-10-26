#!/bin/bash
# First real integration of a Codex transfer on a third, isolated engine copy.
# usage: codex_intake.sh <transfer-dir> <empty-workdir> <original-engine-clone> <our-bundle.json> [our-classification.json]
# transfer-dir must hold: codex-coverage-snapshot.json, codex-special-source-evidence.json,
#   codex-engine.bundle (git bundle containing the Codex commit) and SHA256SUMS.txt covering all three.
# Environment: CODEX_SHA (default 65447bd55e565181e5c608dd47bd39c88127624d), EXPECT_KEYS, EXPECT_WEIGHTED,
#   EXPECT_CONS_KEYS, EXPECT_CONS_WEIGHTED (Codex's stated figures, reproduced exactly or the run says so).
set -uo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"; IN="$(cd "$1" && pwd)"; WORK="$2"; ENGINE="$3"; OURS="$4"; CLASS="${5:-}"
CODEX_SHA="${CODEX_SHA:-65447bd55e565181e5c608dd47bd39c88127624d}"
mkdir -p "$WORK" && WORK="$(cd "$WORK" && pwd)"; [ -z "$(ls -A "$WORK")" ] || { echo "workdir must be empty" >&2; exit 1; }
T="python3 -I $KIT/tools"; SNAP="$IN/codex-coverage-snapshot.json"; EVID="$IN/codex-special-source-evidence.json"
step() { echo "== $*" | tee -a "$WORK/STEPS.log"; }
fail() { echo "STOP: $*" | tee -a "$WORK/STEPS.log"; exit "${2:-1}"; }

step "0 transfer fingerprints"
( cd "$IN" && sha256sum -c SHA256SUMS.txt ) > "$WORK/0-sha256.txt" 2>&1 || fail "fingerprints do not match (see 0-sha256.txt)" 2
for f in codex-coverage-snapshot.json codex-special-source-evidence.json codex-engine.bundle; do
  [ -f "$IN/$f" ] || fail "missing $f" 2; grep -q " $f\$\| \*$f\$" "$IN/SHA256SUMS.txt" || fail "$f not covered by SHA256SUMS.txt" 2; done

step "1 contract-validate"
$T/snapshot_tool.py validate "$SNAP" > "$WORK/1-validate.json" || fail "snapshot is not a valid bundle (see 1-validate.json)" 2

step "2 reproduce Codex figures from the snapshot records"
$T/reproduce.py "$SNAP" ${EXPECT_KEYS:+--expect-keys "$EXPECT_KEYS"} ${EXPECT_WEIGHTED:+--expect-weighted "$EXPECT_WEIGHTED"} \
  ${EXPECT_CONS_KEYS:+--expect-conservative-keys "$EXPECT_CONS_KEYS"} ${EXPECT_CONS_WEIGHTED:+--expect-conservative-weighted "$EXPECT_CONS_WEIGHTED"} \
  > "$WORK/2-reproduce.json"; echo "reproduction exit $? (0 = every stated figure reproduced)" | tee -a "$WORK/STEPS.log"

step "3 contract-compare: our bundle vs Codex"
cp "$OURS" "$WORK/ours-bundle.json"
$T/snapshot_tool.py compare "$OURS" "$SNAP" --out "$WORK/3-compare-ours-codex.json" > "$WORK/3-summary.json" || fail "compare refused" 2

step "4 special-source evidence"
$T/evidence_check.py "$EVID" "$SNAP" ${CLASS:+"$CLASS"} > "$WORK/4-evidence.json" || fail "evidence file unreadable" 2

step "5 third engine copy at the Codex commit"
E="$WORK/integration-engine"; git clone -q --no-hardlinks "$ENGINE" "$E" || fail "clone failed"
git -C "$E" bundle verify "$IN/codex-engine.bundle" > "$WORK/5-bundle-verify.txt" 2>&1 || fail "codex bundle prerequisites missing (see 5-bundle-verify.txt)" 3
git -C "$E" fetch -q "$IN/codex-engine.bundle" "+refs/*:refs/codex/*" || fail "fetch of codex bundle failed" 3
git -C "$E" cat-file -e "$CODEX_SHA^{commit}" 2>/dev/null || fail "commit $CODEX_SHA is not in the codex bundle" 3
git -C "$E" checkout -q -b integration/codex "$CODEX_SHA"
git -C "$E" diff --stat "$(git -C "$E" merge-base HEAD origin/HEAD 2>/dev/null || git -C "$E" rev-list --max-parents=0 HEAD | tail -1)" HEAD -- data/imports config > "$WORK/5-codex-data-changes.txt" 2>/dev/null
ls "$E/config/factory/field-availability/"*.json > "$WORK/5-codex-assessments.txt" 2>/dev/null || true
FA_EMPTY="$WORK/no-assessments"; mkdir -p "$FA_EMPTY"

build() {  # build <label> <field-availability-dir>
  local L="$1" FA="$2"
  ( cd "$E" && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
    python3 -m finengine --db "$WORK/$L.sqlite3" bootstrap --imports data/imports --registry config/companies.json \
      --raw-dir "$WORK/raw-$L" --html "$WORK/$L.html" --csv "$WORK/$L.csv" --field-availability-dir "$FA" > "$WORK/$L-bootstrap.log" 2>&1 \
      || { echo "bootstrap failed for $L" >&2; exit 1; }
    python3 -m finengine --db "$WORK/$L.sqlite3" factory-contract-readiness SA 2222 > "$WORK/$L-ready.json"
    python3 "$KIT/tools/export_from_engine.py" "$WORK/$L.sqlite3" sa:2222 "$WORK/$L-bundle.json" "$L@$(git rev-parse --short HEAD)" "$(git rev-parse HEAD)" > "$WORK/$L-export.json" )
}
step "6 before: rebuild at the Codex commit (its own assessments: reproduction only; none: official)"
build before-codex-assessments "$E/config/factory/field-availability" & build before "$FA_EMPTY" & wait
[ -f "$WORK/before-bundle.json" ] || fail "before build failed (see before-bootstrap.log)" 4

step "7 apply the correctness pack on the integration branch"
git -C "$E" fetch -q "$KIT/git/correctness-pack.bundle" "refs/heads/fixes/correctness-pack:fixes/correctness-pack" || fail "pack bundle fetch failed" 3
if ! git -C "$E" -c user.name=Claude -c user.email=noreply@anthropic.com merge -q --no-ff fixes/correctness-pack \
      -m "Integrate the correctness pack onto Codex $CODEX_SHA" > "$WORK/7-merge.txt" 2>&1; then
  git -C "$E" diff --name-only --diff-filter=U > "$WORK/7-merge-conflicts.txt"; git -C "$E" merge --abort
  fail "merge conflicts need a decision (see 7-merge-conflicts.txt); nothing was resolved automatically" 5
fi
git -C "$E" rev-parse HEAD > "$WORK/INTEGRATION_SHA"
( cd "$E" && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 timeout 2400 python3 -m unittest discover -s tests > "$WORK/7-tests.log" 2>&1 ); tail -n 3 "$WORK/7-tests.log" | tee -a "$WORK/STEPS.log"

step "8 after: rebuild with the pack (no unsigned assessments)"
build after "$FA_EMPTY"; [ -f "$WORK/after-bundle.json" ] || fail "after build failed (see after-bootstrap.log)" 4
( cd "$E" && PYTHONPATH=src python3 "$KIT/tools/run_impact.py" "$WORK/before.sqlite3" "$WORK/after.sqlite3" "pack@$(git rev-parse --short fixes/correctness-pack)" > "$WORK/8-engine-impact.json" )

step "9 measure from the unified records, compare, escalate"
$T/reproduce.py "$WORK/after-bundle.json" > "$WORK/9-after-coverage.json"
$T/reproduce.py "$WORK/before-bundle.json" > "$WORK/9-before-coverage.json"
$T/reproduce.py "$WORK/before-codex-assessments-bundle.json" > "$WORK/9-before-with-codex-assessments-coverage.json" 2>/dev/null
$T/snapshot_tool.py compare "$WORK/before-bundle.json" "$WORK/after-bundle.json" --out "$WORK/9-before-vs-after.json" > /dev/null
$T/snapshot_tool.py compare "$OURS" "$WORK/after-bundle.json" --out "$WORK/9-ours-vs-integration.json" > /dev/null
$T/snapshot_tool.py compare "$WORK/after-bundle.json" "$SNAP" --out "$WORK/9-integration-vs-codex.json" > /dev/null
$T/escalate.py "ours=$WORK/3-compare-ours-codex.json" "integration=$WORK/9-integration-vs-codex.json" > "$WORK/9-escalations.json"
python3 "$KIT/tools/integration_summary.py" "$WORK" > "$WORK/SUMMARY.json"; cat "$WORK/SUMMARY.json" | tee -a "$WORK/STEPS.log"
