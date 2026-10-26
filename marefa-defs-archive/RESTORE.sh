#!/bin/bash
# Restore both branches into a fresh, isolated clone of the original engine and verify them.
# usage: RESTORE.sh <path-to-original-engine-clone> <empty-target-dir>
set -euo pipefail
A="$(cd "$(dirname "$0")" && pwd)"; SRC="$1"; DST="$2"
git clone -q --no-hardlinks "$SRC" "$DST"; cd "$DST"
git cat-file -e b70254e463c18e893fd042a82ecdad78209384d6^{commit}
git fetch -q "$A/git/defs-independent-validation.bundle" "refs/heads/defs/independent-validation:defs/independent-validation"
git fetch -q "$A/git/correctness-pack.bundle" "refs/heads/fixes/correctness-pack:fixes/correctness-pack"
test "$(git rev-parse defs/independent-validation)" = 271f145297f5b027ec9258fafc7de0ec34bd32a5
test "$(git rev-parse fixes/correctness-pack)" = f7593d5cc2cfb9ffc8414930b6abdb1b174ffa38
echo "restored: defs/independent-validation and fixes/correctness-pack in $DST"
