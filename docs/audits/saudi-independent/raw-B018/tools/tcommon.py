"""Shared helpers for building transcripts (batch B018)."""
import json
from pathlib import Path

TR = Path(__file__).resolve().parent.parent / "transcripts"


def bs(ta, tl, te, cash, ppe=None, **k):
    d = dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, **k)
    if ppe is not None:
        d["ppe"] = ppe
    return d


def cf(cfo, cfi, cff, net, b, e, **k):
    return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)


def inc(rev, pbt, tax, ni, **k):
    d = dict(pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)
    if rev is not None:
        d["revenue"] = rev
    return d


def write(sym, name, docs, rolls=None, unit="SAR thousands as printed (SAR '000)"):
    t = dict(symbol=sym, name=name, currency="SAR", unit=unit, docs=docs, roll_checks=rolls or [])
    (TR / f"{sym}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print("wrote", sym, len(docs), "docs")
