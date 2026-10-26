"""Reproduce a snapshot's own coverage figures from its records (no engine needed).

usage: python3 reproduce.py SNAPSHOT.json [--expect-keys N/M] [--expect-weighted PCT] [--expect-conservative-keys N]
       [--expect-conservative-weighted PCT]
Distinct keys, slots and the engine's weighted formula are recomputed from the records. A
conservative figure is reproduced only from an explicit per-record marker; without one it is
reported as not reproducible rather than guessed.
"""
import argparse, json, sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_compare import checked_bundle, contract_score  # noqa: E402

MARKERS = ("conservative", "is_conservative", "conservative_closed", "tier", "acceptance", "accepted")

parser = argparse.ArgumentParser()
parser.add_argument("snapshot")
parser.add_argument("--expect-keys"); parser.add_argument("--expect-weighted")
parser.add_argument("--expect-conservative-keys"); parser.add_argument("--expect-conservative-weighted")
args = parser.parse_args()
bundle = checked_bundle(json.loads(Path(args.snapshot).read_text(encoding="utf-8")))
closed = {r["key"] for r in bundle["records"] if r["status"] == "closed"}
keys = {f["key"] for c in bundle["contract"]["categories"] for f in c.get("fields", [])}
slots = sum(len(c.get("fields", [])) for c in bundle["contract"]["categories"])
weight = sum(Decimal(str(c["weight"])) for c in bundle["contract"]["categories"])
score = contract_score(bundle, closed)
out = {"distinct_keys": f"{len(closed & keys)}/{len(keys)}", "slots": slots,
       "weighted": str(score), "weighted_pct_of_total_weight": str(score / weight * 100)}
markers = sorted({m for r in bundle["records"] for m in MARKERS if m in r})
stated = {k: bundle[k] for k in bundle if k not in ("contract", "records")}
out["stated_by_snapshot"] = stated
if markers:
    def conservative(record):
        value = next(record[m] for m in markers if m in record)
        return value is True or str(value).lower() in ("conservative", "true", "accepted", "yes")
    kept = {r["key"] for r in bundle["records"] if r["status"] == "closed" and any(m in r for m in markers) and conservative(r)}
    out["conservative"] = {"marker_fields": markers, "distinct_keys": f"{len(kept & keys)}/{len(keys)}",
                           "weighted": str(contract_score(bundle, kept))}
else:
    out["conservative"] = {"status": "not_reproducible", "reason": "no per-record conservative marker in the snapshot"}
checks = []
def check(label, expected, actual):
    if expected is not None:
        ok = (Decimal(expected) - Decimal(actual)).copy_abs() <= Decimal("0.000001") if "/" not in expected else expected == actual
        checks.append({"check": label, "expected": expected, "reproduced": actual, "match": ok})
check("keys", args.expect_keys, out["distinct_keys"])
check("weighted", args.expect_weighted, out["weighted_pct_of_total_weight"])
if "distinct_keys" in out["conservative"]:
    check("conservative keys", args.expect_conservative_keys and f"{args.expect_conservative_keys}/{len(keys)}",
          out["conservative"]["distinct_keys"])
    check("conservative weighted", args.expect_conservative_weighted,
          str(Decimal(out["conservative"]["weighted"]) / weight * 100))
out["checks"] = checks
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
sys.exit(0 if all(c["match"] for c in checks) else 1)
