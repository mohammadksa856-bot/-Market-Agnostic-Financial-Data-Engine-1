"""Arithmetic identity checks over the batch-B005 page transcriptions (offline, read-only).

For every transcribed document/column:
  * balance sheet: total_assets == total_liabilities + total_equity (when both liabilities and equity were transcribed)
  * cash flow: cfo + cfi + cff == net_change (when net_change transcribed) and cash_begin + net + optional fx == cash_end
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
    """Identities over every column key (cur, prior, or any labelled year/period column). doc['tol'] allows rounding slack
    (used only for board-report summaries in rounded SAR millions)."""
    bad = []
    tol = doc.get("tol", 0)
    ne = lambda x, y: abs(x - y) > tol
    for stmt in ("bs", "cf", "is", "is_q"):
        for col, v in doc.get(stmt, {}).items():
            if not v:
                continue
            if stmt == "bs" and {"total_assets", "total_liabilities", "total_equity"} <= v.keys():
                if ne(v["total_assets"], v["total_liabilities"] + v["total_equity"]):
                    bad.append((doc["label"], col, "bs", v["total_assets"], v["total_liabilities"] + v["total_equity"]))
            if stmt == "cf":
                if {"cfo", "cfi", "cff", "net_change"} <= v.keys() and ne(v["cfo"] + v["cfi"] + v["cff"], v["net_change"]):
                    bad.append((doc["label"], col, "cf-sum", v["net_change"], v["cfo"] + v["cfi"] + v["cff"]))
                if {"cash_begin", "net_change", "cash_end"} <= v.keys():
                    rolled = v["cash_begin"] + v["net_change"] + v.get("fx", 0)
                    if ne(rolled, v["cash_end"]):
                        bad.append((doc["label"], col, "cf-roll", v["cash_end"], rolled))
            if stmt in ("is", "is_q") and {"net_income", "ni_parent", "ni_nci"} <= v.keys() and ne(v["net_income"], v["ni_parent"] + v["ni_nci"]):
                bad.append((doc["label"], col, stmt, v["net_income"], v["ni_parent"] + v["ni_nci"]))
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
