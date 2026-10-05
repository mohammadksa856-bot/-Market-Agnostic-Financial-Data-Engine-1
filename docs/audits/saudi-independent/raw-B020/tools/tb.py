"""tb.py: tiny helper for building page-transcript JSON for batch B020 (offline). Values are typed from page images or clean text layers
viewed in the audit session; this module only assembles structure and adds _extra_keys so cross-filing checks also cover non-standard lines."""
import json
from pathlib import Path

TR = Path(__file__).resolve().parent.parent / "transcripts"


def col(**kw):
    return {k: v for k, v in kw.items() if v is not None}


def doc(sha, label, period_end, prior_end, ptype, reading, pages, bs=None, is_=None, isq=None, cf=None, bs_prior_end=None, extra=None, **more):
    d = {"sha256_prefix": sha, "label": label, "period_end": period_end, "prior_end": prior_end, "period_type": ptype,
         "reading": reading, "pages": pages}
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    for key, v in (("bs", bs), ("is", is_), ("is_q", isq), ("cf", cf)):
        if v:
            d[key] = {"cur": dict(v[0]), "prior": dict(v[1])} if v[1] is not None else {"cur": dict(v[0])}
            if extra:
                for c in d[key].values():
                    ek = [k for k in extra if k in c]
                    if ek:
                        c["_extra_keys"] = ek
    d.update(more)
    return d


def write(symbol, name, currency, unit, docs, rolls=None, notes=None):
    t = {"symbol": symbol, "name": name, "currency": currency, "unit": unit, "docs": docs}
    if rolls:
        t["roll_checks"] = rolls
    if notes:
        t["notes"] = notes
    (TR / f"{symbol}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print(symbol, "docs", len(docs))


def roll(name, total, parts, tol=0):
    """total/parts = (sha_prefix, block, col, key)"""
    return {"name": name, "total": list(total), "parts": [list(p) for p in parts], "tol": tol}
