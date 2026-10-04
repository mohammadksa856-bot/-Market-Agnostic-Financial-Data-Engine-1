"""Helpers for visually read (manual) transcript documents."""


def I(rev, cost, gp, pbt, tax, ni, parent, nci, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, pbt=pbt, tax=tax, net_income=ni, ni_parent=parent, ni_nci=nci)
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


def C(cfo, cfi, cff, net, begin, fx, end, capex=None, **k):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=begin, fx=fx, cash_end=end)
    if capex is not None:
        d["capex"] = capex
    d.update(k)
    return d


def doc(sha, label, pe, pt, reading, pages, printed, bs, is_, cf, is_q=None, scale=1, bs_prior_end=None, **k):
    py = f"{int(pe[:4]) - 1}{pe[4:]}"
    d = {"sha256_prefix": sha, "label": label, "period_end": pe, "prior_end": py, "period_type": pt, "reading": reading,
         "pages": pages, "printed_pages": printed, "bs": bs, "is": is_, "cf": cf, "scale": scale,
         "bs_prior_end": bs_prior_end or (py if pt == "FY" else f"{int(pe[:4]) - 1}-12-31")}
    if is_q:
        d["is_q"] = is_q
    d.update(k)
    return d


VIS = "visual: image-only statement pages rendered and read"
