"""Shared helpers for building page-transcript JSON files."""
import json
import pathlib


def I(rev, cost, gp, pbt, tax, ni, parent=None, nci=0, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, pbt=pbt, tax=tax, net_income=ni,
             ni_parent=ni - nci if parent is None else parent, ni_nci=nci)
    if eps is not None:
        d["eps"] = eps
    d.update(k)
    return d


def B(ta, tl, te, cash, ppe=None, **k):
    d = dict(total_assets=ta, total_equity=te, cash=cash)
    if tl is not None:
        d["total_liabilities"] = tl
    if ppe is not None:
        d["ppe"] = ppe
    d.update(k)
    return d


def C(cfo, capex, cfi, cff, net, begin, end, **k):
    d = dict(cfo=cfo, capex=capex, cfi=cfi, cff=cff, net_change=net, cash_begin=begin, cash_end=end)
    d.update(k)
    return d


def doc(prefix, label, pe, pr, ptype, reading, pages, bs, is_, cf, bs_prior_end=None, is_q=None):
    d = dict(sha256_prefix=prefix, label=label, period_end=pe, prior_end=pr, period_type=ptype, reading=reading,
             pages=pages, bs=bs, cf=cf)
    d["is"] = is_
    if is_q:
        d["is_q"] = is_q
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    return d


def ref(p, block, col, key):
    return [p, block, col, key]


def write(sym, name, unit, docs, rolls=()):
    out = dict(symbol=sym, name=name, currency="SAR", unit=unit, docs=docs, roll_checks=list(rolls))
    pathlib.Path(__file__).resolve().parent.parent.joinpath("transcripts", f"{sym}.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print("written", sym, len(docs))
