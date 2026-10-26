"""Round-2 classification of the 72 definition keys and 20 open unproven keys (keys and points only)."""
import json, sys
from decimal import Decimal
sys.path.insert(0, "tools"); from missing import missing

prev = json.load(open("deliver/KEY-CLASSIFICATION.json"))
_, final = missing("runs/r10/ready.json")
pts = {}
for _, _, k, p in final: pts[k] = pts.get(k, Decimal(0)) + p
_, before = missing("runs/r6-final/ready.json")
pts_before = {}
for _, _, k, p in before: pts_before[k] = pts_before.get(k, Decimal(0)) + p
draft = {a["field_key"]: a for a in json.load(open("fa-draft/2222.json"))["assessments"]}

CLOSED = {"dividend_per_share_ttm": "D13", "total_dividend_paid_ttm": "D13", "dividend_payment_frequency": "UNPROVEN"}
WITHHELD = {"dividend_cagr_3y": "share-basis audit: DPS 2022 from AR2022 precedes the 2023 bonus issue"}
TO_NEEDS_PERIOD = {"payout_ratio_ttm": "engine payout definition exists; 2025 quarterly net income missing",
                   "fcf_payout_ratio_ttm": "engine FCF payout definition exists; 2025 quarterly FCF missing"}
TO_DECISIONS = {"contingencies": "note 33 (PDF 230-231) gives guarantee amounts; which make up 'contingencies' is a definition"}

def_keys = {k for g in prev["definitions_open"] for k in g["keys"]}
unproven = {u["key"]: u for u in prev["unproven_open"]}
assert set(CLOSED) - {"dividend_payment_frequency"} <= def_keys and "dividend_payment_frequency" in unproven
for k in CLOSED: assert k in pts_before and k not in pts, k
for k in WITHHELD: assert k in pts and k not in pts_before, k
for k in draft: assert k in pts, k

out = {"basis": {"engine": "80dea99 (defs/independent-validation, local)", "slots": 717, "distinct_keys": 685,
                 "score": "65.8916", "closed_slots": 493, "closed_distinct_keys": 469},
       "closed_this_round": [{"key": k, "from": s, "points": f"{pts_before[k]:.4f}"} for k, s in CLOSED.items()],
       "withheld_this_round": [{"key": k, "reason": r, "points": f"{pts[k]:.4f}"} for k, r in WITHHELD.items()],
       "awaiting_signature": [{"key": k, "status": a["status"], "reason_code": a["reason_code"],
                               "points_if_signed": f"{pts[k]:.4f}", "note": a.get("evidence_note", "")} for k, a in draft.items()]}
groups = []
for g in prev["definitions_open"]:
    keys = [k for k in g["keys"] if k not in CLOSED and k not in draft and k not in TO_NEEDS_PERIOD]
    if keys:
        groups.append({"decision": g["decision"], "keys": keys, "points": f"{sum(pts[k] for k in keys):.4f}"})
groups.append({"decision": "D18_contingencies_total", "keys": list(TO_DECISIONS), "points": f"{sum(pts[k] for k in TO_DECISIONS):.4f}"})
out["definitions_needing_decision"] = groups
needs_period = [k for k, u in unproven.items() if u["class"] == "needs_period"] + list(TO_NEEDS_PERIOD)
out["needs_period"] = [{"key": k, "points": f"{pts[k]:.4f}", "reason": unproven[k]["reason"] if k in unproven else TO_NEEDS_PERIOD[k]} for k in needs_period]
dec_keys = [k for g in groups for k in g["keys"]]
out["summary"] = {
    "def_set_start": 72, "def_closed": 2, "def_awaiting_signature": len([k for k in draft if k in def_keys]),
    "def_moved_to_needs_period": len(TO_NEEDS_PERIOD), "def_still_needing_decision": len([k for k in dec_keys if k in def_keys]),
    "unproven_start": 20, "unproven_closed": 1, "unproven_awaiting_signature": len([k for k in draft if k in unproven]),
    "unproven_moved_to_decisions": 1, "unproven_still_needs_period": len([k for k in needs_period if k in unproven]),
    "keys_needing_decision_total": len(dec_keys), "decision_points": f"{sum(pts[k] for k in dec_keys):.4f}",
    "needs_period_points": f"{sum(pts[k] for k in needs_period):.4f}",
    "if_signed_points_gain": "3.3008 (65.8916 -> 69.1924, denominator 717 -> 688 slots)"}
assert out["summary"]["def_closed"] + out["summary"]["def_awaiting_signature"] + 2 + out["summary"]["def_still_needing_decision"] == 72
json.dump(out, open("deliver/KEY-CLASSIFICATION-R2.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out["summary"], indent=1)); print({g["decision"]: (len(g["keys"]), g["points"]) for g in groups})
