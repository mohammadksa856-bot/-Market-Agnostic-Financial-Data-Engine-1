"""Arithmetic and cross-filing checks over the batch-B012 page transcriptions (offline, read-only).

Per document column (cur / prior):
  * balance sheet: total_assets == total_liabilities + total_equity (when both liabilities and equity transcribed)
  * cash flow: cfo + cfi + cff == net_change; cash_begin + net_change + fx == cash_end
  * income ('is' and 'is_q'): net_income == ni_parent + ni_nci
Cross-document: columns that describe the same block and period end (doc period_end for 'cur', doc prior_end for 'prior')
must agree on revenue, net_income, ni_parent, cfo, cfi, cff, net_change, total_assets, total_equity, ppe, cash_end, unless the later column is flagged
"restated": true (then the difference is expected and must be listed in the document's "restatements").
Roll checks (transcript key "roll_checks"): total == sum(parts) within tol (Q1 + Q2 = H1 etc.).
Every sha256_prefix must exist in the raw-coverage inventory.
Usage: python check_transcripts.py [symbol ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT.parent / "raw-coverage" / "companies"
TR = ROOT / "transcripts"
XKEYS = ("revenue", "net_income", "ni_parent", "cfo", "cfi", "cff", "net_change", "total_assets", "total_equity", "ppe", "cash_end",
         "cost_of_revenue", "gross_profit", "operating_income", "pbt")


def identities(doc):
    bad = []
    for col in ("cur", "prior"):
        bs = doc.get("bs", {}).get(col)
        if bs and {"total_assets", "total_liabilities", "total_equity"} <= bs.keys():
            if bs["total_assets"] != bs["total_liabilities"] + bs["total_equity"]:
                bad.append((doc["label"], col, "bs", bs["total_assets"], bs["total_liabilities"] + bs["total_equity"]))
        cf = doc.get("cf", {}).get(col)
        if cf:
            if {"cfo", "cfi", "cff", "net_change"} <= cf.keys() and cf["cfo"] + cf["cfi"] + cf["cff"] != cf["net_change"]:
                bad.append((doc["label"], col, "cf-sum", cf["net_change"], cf["cfo"] + cf["cfi"] + cf["cff"]))
            if {"cash_begin", "net_change", "cash_end"} <= cf.keys():
                rolled = cf["cash_begin"] + cf["net_change"] + cf.get("fx", 0)
                if rolled != cf["cash_end"]:
                    bad.append((doc["label"], col, "cf-roll", cf["cash_end"], rolled))
        for key in ("is", "is_q"):
            i = doc.get(key, {}).get(col)
            if i and {"net_income", "ni_parent", "ni_nci"} <= i.keys() and abs(i["net_income"] - i["ni_parent"] - i["ni_nci"]) > doc.get("tol", 0):
                bad.append((doc["label"], col, key, i["net_income"], i["ni_parent"] + i["ni_nci"]))
            if i and {"revenue", "cost_of_revenue", "gross_profit"} <= i.keys() and i["revenue"] + i["cost_of_revenue"] != i["gross_profit"]:
                bad.append((doc["label"], col, key + "-gross", i["gross_profit"], i["revenue"] + i["cost_of_revenue"]))
            if i and {"pbt", "tax", "net_income"} <= i.keys() and i["pbt"] + i["tax"] + i.get("discontinued", 0) != i["net_income"]:
                bad.append((doc["label"], col, key + "-tax", i["net_income"], i["pbt"] + i["tax"] + i.get("discontinued", 0)))
    return bad


def cross(docs):
    seen = {}
    bad = []
    for d in docs:
        for block in ("bs", "is", "is_q", "cf"):
            for col in ("cur", "prior"):
                c = d.get(block, {}).get(col)
                if not c:
                    continue
                end = d["period_end"] if col == "cur" else (d.get("bs_prior_end") if block == "bs" and d.get("bs_prior_end") else d.get("prior_end"))
                if end is None:
                    continue
                for k in XKEYS + tuple(c.get("_extra_keys", [])):
                    if k in c:
                        key = (block, end, k)
                        sv = c[k] * d.get("scale", 1)
                        if key in seen and seen[key][0] != sv and not c.get("restated") and not seen[key][2]:
                            bad.append((d["label"], block, col, k, sv, "vs", seen[key][1], seen[key][0]))
                        seen.setdefault(key, (sv, d["label"], bool(c.get("restated"))))
    return bad


def rolls(t):
    bad = []
    byp = {d["sha256_prefix"]: d for d in t["docs"]}
    for r in t.get("roll_checks", []):
        def val(ref):
            p, block, col, key = ref
            return byp[p][block][col][key]
        tot = val(r["total"])
        s = sum(val(x) for x in r["parts"])
        if abs(tot - s) > r.get("tol", 0):
            bad.append((r["name"], tot, s))
    return bad


def check(symbol):
    t = json.loads((TR / f"{symbol}.json").read_text(encoding="utf8"))
    inv = json.loads((INV / f"{symbol}.json").read_text(encoding="utf8"))
    shas = {f["sha256"] for f in inv["files"]}
    problems = []
    for d in t["docs"]:
        if not any(s.startswith(d["sha256_prefix"]) for s in shas):
            problems.append((d["label"], "sha not in inventory"))
        problems += identities(d)
    problems += cross(t["docs"])
    problems += rolls(t)
    return t, problems


if __name__ == "__main__":
    syms = sys.argv[1:] or sorted(p.stem for p in TR.glob("*.json"))
    rc = 0
    for s in syms:
        t, p = check(s)
        print(s, "docs", len(t["docs"]), "problems", p)
        rc |= bool(p)
    sys.exit(rc)
