"""Shared helpers for batch-B019 page transcriptions (builders only; every value is typed by hand from a viewed page)."""
import json
from pathlib import Path

TR = Path(__file__).resolve().parent.parent / "transcripts"


def bs(ta, tl, te, cash=None, ppe=None, **k):
    d = dict(total_assets=ta, total_liabilities=tl, total_equity=te, **k)
    if cash is not None:
        d["cash"] = cash
    if ppe is not None:
        d["ppe"] = ppe
    return d


def cf(cfo, cfi, cff, net, b, e, fx=None, **k):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)
    if fx:
        d["fx"] = fx
    return d


def inc(rev, cost, gp, op, pbt, tax, ni, par=None, nci=None, disc=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, **k)
    if disc is not None:
        d["discontinued"] = disc
    if par is not None:
        d["ni_parent"] = par
        d["ni_nci"] = nci
    return d


def doc(sha, label, pe, pre, ptype, reading, pages, bs_=None, is_=None, isq=None, cf_=None, bs_prior_end=None, **k):
    d = dict(sha256_prefix=sha, label=label, period_end=pe, prior_end=pre, period_type=ptype, reading=reading, pages={('is' if kk == 'is_' else kk): vv for kk, vv in pages.items()})
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    if bs_:
        d["bs"] = bs_
    if is_:
        d["is"] = is_
    if isq:
        d["is_q"] = isq
    if cf_:
        d["cf"] = cf_
    d.update(k)
    return d


def write(sym, name, currency, unit, docs, roll_checks=None):
    t = dict(symbol=sym, name=name, currency=currency, unit=unit, docs=docs)
    if roll_checks:
        t["roll_checks"] = roll_checks
    (TR / f"{sym}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print(sym, "docs", len(docs))
