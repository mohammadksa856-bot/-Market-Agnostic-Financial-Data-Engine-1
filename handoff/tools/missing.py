"""Per-key missing points from a factory-contract-readiness JSON: points = weight / expected_fields."""
import json, sys
from decimal import Decimal

def missing(path):
    d = json.load(open(path)); out = []
    for c in d["categories"]:
        ev = c.get("evidence", {}); exp = int(ev.get("expected_fields") or 0)
        if not exp:
            continue
        pts = Decimal(c["weight"]) / exp
        for group, keys in (ev.get("missing_fields") or {}).items():
            out += [(c["category_key"], group, k, pts) for k in keys]
    return Decimal(d["total_score"]), out

if __name__ == "__main__":
    a_score, a = missing(sys.argv[1]); b_score, b = missing(sys.argv[2])
    ka = {(c, g, k) for c, g, k, _ in a}; kb = {(c, g, k) for c, g, k, _ in b}
    pa = {(c, g, k): p for c, g, k, p in a}; pb = {(c, g, k): p for c, g, k, p in b}
    print(f"score {a_score:.4f} -> {b_score:.4f} ({b_score - a_score:+.4f}); missing {len(a)} -> {len(b)}")
    for key in sorted(ka - kb): print("  closed ", key, f"{pa[key]:.4f}")
    for key in sorted(kb - ka): print("  opened ", key, f"{pb[key]:.4f}")
