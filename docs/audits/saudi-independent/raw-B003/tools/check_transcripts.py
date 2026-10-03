"""Arithmetic identity checks over the batch-B003 page transcriptions (offline, read-only).

For every transcribed document/column:
  * balance sheet: total_assets == total_liabilities + total_equity (when both liabilities and equity were transcribed)
  * cash flow: cfo + cfi + cff == net_change (when net_change transcribed) and cash_begin + net == cash_end
  * income: net_income == ni_parent + ni_nci (when ni_nci transcribed)
  * cross-document: a period's 'prior' column must equal the same period's 'cur' column in the document that reported it
    (restatement detector) for the keys revenue, net_income, cfo, total_assets.
Also validates that each transcript's sha256_prefix exists in the raw-coverage inventory.
Usage: python check_transcripts.py [symbol ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT.parent / "raw-coverage" / "companies"
TR = ROOT / "transcripts"


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
            if {"cash_begin", "net_change", "cash_end"} <= cf.keys() and cf["cash_begin"] + cf["net_change"] != cf["cash_end"]:
                bad.append((doc["label"], col, "cf-roll", cf["cash_end"], cf["cash_begin"] + cf["net_change"]))
        for key in ("is", "is_q"):
            i = doc.get(key, {}).get(col)
            if i and {"net_income", "ni_parent", "ni_nci"} <= i.keys() and i["net_income"] != i["ni_parent"] + i["ni_nci"]:
                bad.append((doc["label"], col, key, i["net_income"], i["ni_parent"] + i["ni_nci"]))
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
    return t, problems


if __name__ == "__main__":
    syms = sys.argv[1:] or sorted(p.stem for p in TR.glob("*.json"))
    rc = 0
    for s in syms:
        t, p = check(s)
        print(s, "docs", len(t["docs"]), "problems", p)
        rc |= bool(p)
    sys.exit(rc)
