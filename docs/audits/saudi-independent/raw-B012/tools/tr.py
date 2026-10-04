"""Build transcripts/<symbol>.json from auto_<symbol>.json (text-layer extraction) plus manual_<symbol>.json (visually read docs)
and meta_<symbol>.json (currency/unit, per-file patches for image-only pages inside text files, extra roll checks, restatement declarations).
Usage: tr.py <symbol> [autodir]   -- prints a compact review table and the checker result."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_transcripts as ct

MAP = {"parent": "ni_parent", "nci": "ni_nci"}


def blk(d, i):
    return {MAP.get(k, k): v[i] for k, v in d.items()}


def norm(b):
    notes = []
    if {"revenue", "cost_of_revenue", "gross_profit"} <= b.keys() and b["cost_of_revenue"] > 0 and b["revenue"] - b["cost_of_revenue"] == b["gross_profit"]:
        b["cost_of_revenue"] = -b["cost_of_revenue"]
        notes.append("cost sign")
    if {"pbt", "tax", "net_income"} <= b.keys() and b["tax"] > 0 and b["pbt"] - b["tax"] == b["net_income"]:
        b["tax"] = -b["tax"]
        notes.append("tax sign")
    return notes


def rolls(docs):
    out = []
    by = {}
    for d in docs:
        by.setdefault((d["period_end"][:4], d["period_type"]), []).append(d)
    for y in sorted({k[0] for k in by}):
        q1, h1, m9 = by.get((y, "Q1")), by.get((y, "H1")), by.get((y, "9M"))
        for key in ("revenue", "net_income", "pbt", "gross_profit"):
            if q1 and h1 and "is_q" in h1[0] and key in q1[0]["is"]["cur"] and key in h1[0]["is_q"]["cur"] and key in h1[0]["is"]["cur"]:
                out.append({"name": f"{y} Q1 + Q2 = H1 {key}", "total": [h1[0]["sha256_prefix"], "is", "cur", key],
                            "parts": [[q1[0]["sha256_prefix"], "is", "cur", key], [h1[0]["sha256_prefix"], "is_q", "cur", key]], "tol": 2})
            if h1 and m9 and "is_q" in m9[0] and key in h1[0]["is"]["cur"] and key in m9[0]["is_q"]["cur"] and key in m9[0]["is"]["cur"]:
                out.append({"name": f"{y} H1 + Q3 = 9M {key}", "total": [m9[0]["sha256_prefix"], "is", "cur", key],
                            "parts": [[h1[0]["sha256_prefix"], "is", "cur", key], [m9[0]["sha256_prefix"], "is_q", "cur", key]], "tol": 2})
    return out


def prior_year(d):
    return f"{int(d[:4]) - 1}{d[4:]}"


def build(sym, auto):
    docs, skipped = [], []
    for r in auto:
        if "textless" in r["flags"] or not all(r.get(k) for k in ("is", "bs", "cf")) or not r.get("period_end") or r["period_type"] == "?":
            skipped.append((r["label"], r["sha"][:8], r["cls"], r["flags"]))
            continue
        pt = r["period_type"]
        pe = r["period_end"]
        d = {"sha256_prefix": r["sha"][:8], "label": f"{r['label']} auto text-layer", "period_end": pe, "prior_end": prior_year(pe),
             "period_type": "Q1" if pt == "Q" and pe[5:7] == "03" else pt,
             "reading": "text layer, rows rebuilt from word coordinates (tools/auto.py)" + ("; " + r["patched"] if r.get("patched") else ""),
             "pages": {k: v for k, v in r["pdf"].items()}, "printed_pages": {"bs": r.get("printed_bs"), "is": r.get("printed_is"), "cf": r.get("printed_cf")},
             "bs_prior_end": prior_year(pe) if pt == "FY" else f"{int(pe[:4]) - 1}-12-31", "scale": 1000 if r.get("unit_hint") else 1, "sign_notes": []}
        iss = r["is"]
        if pt in ("H1", "9M"):
            d["is_q"] = {"cur": blk(iss, 0), "prior": blk(iss, 1)}
            d["is"] = {"cur": blk(iss, 2), "prior": blk(iss, 3)}
        else:
            d["is"] = {"cur": blk(iss, 0), "prior": blk(iss, 1)}
        d["bs"] = {"cur": blk(r["bs"], 0), "prior": blk(r["bs"], 1)}
        d["cf"] = {"cur": blk(r["cf"], 0), "prior": blk(r["cf"], 1)}
        for b in ("is", "is_q"):
            for c in ("cur", "prior"):
                if b in d:
                    d["sign_notes"] += norm(d[b][c])
        for c in ("cur", "prior"):
            cf = d["cf"][c]
            if "capex" in cf and cf["capex"] > 0:
                cf["capex"] = -cf["capex"]
        pp = d["printed_pages"]
        offs = {(d["pages"][k][0] if isinstance(d["pages"][k], list) else d["pages"][k]) - pp[k] for k in pp if pp.get(k) is not None and d["pages"].get(k)}
        if not (len(offs) == 1 and all(pp.get(k) is not None for k in ("bs", "is", "cf")) and min(offs) >= 0):
            d["printed_pages"] = {"bs": None, "is": None, "cf": None}
            d["printed_pages_note"] = "printed page numbers not reliably recoverable from the text layer (footer overlaid by signatures or inconsistent); not asserted"
        docs.append(d)
    return docs, skipped


def apply_patches(docs, meta):
    for p in meta.get("doc_patches", []):
        d = next(x for x in docs if x["sha256_prefix"] == p["sha"])
        tgt = d
        for k in p["path"][:-1]:
            tgt = tgt[k]
        if p.get("delete"):
            tgt.pop(p["path"][-1], None)
        else:
            tgt[p["path"][-1]] = p["value"]


if __name__ == "__main__":
    sym = sys.argv[1]
    ad = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("B012_OUT", ".")
    auto = json.load(open(os.path.join(ad, f"auto_{sym}.json"), encoding="utf8"))
    mp0 = HERE / f"meta_{sym}.json"
    meta = json.loads(mp0.read_text(encoding="utf8")) if mp0.exists() else {}
    for r in auto:
        pt = meta.get("patches", {}).get(r["sha"][:8])
        if pt:
            if "bs" in pt:
                r["bs"] = dict(pt["bs"])
                r["pdf"]["bs"] = pt["pdf_bs"]
                r["printed_bs"] = pt.get("printed_bs")
                r["flags"] = [f for f in r["flags"] if "bs" not in f]
                r["bs_end"] = pt.get("bs_end")
            if "cf" in pt:
                r["cf"] = dict(pt["cf"])
                r["pdf"]["cf"] = pt["pdf_cf"]
                r["printed_cf"] = pt.get("printed_cf")
                r["flags"] = [f for f in r["flags"] if "cf" not in f]
            r["patched"] = pt["note"]
    docs, skipped = build(sym, auto)
    off = meta.get("printed_offset")
    if off is not None:
        for d in docs:
            d["printed_pages"] = {k: (v[0] if isinstance(v, list) else v) - off for k, v in d["pages"].items()}
            d["printed_pages_note"] = f"printed page = pdf page - {off} (verified on rendered pages of this company)"
    mp = HERE / f"manual_{sym}.json"
    if mp.exists():
        docs += json.loads(mp.read_text(encoding="utf8"))
    apply_patches(docs, meta)
    inv = json.loads((ct.INV / f"{sym}.json").read_text(encoding="utf8"))
    t = {"symbol": sym, "name": inv["name"], "docs": sorted(docs, key=lambda d: (d["period_end"], d["period_type"], d["sha256_prefix"]))}
    t.update({k: v for k, v in meta.items() if k not in ("patches", "doc_patches", "extra_rolls")})
    t["roll_checks"] = rolls(t["docs"]) + meta.get("extra_rolls", [])
    (ct.TR / f"{sym}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    for d in t["docs"]:
        i = d["is"]["cur"]
        b = d.get("bs", {}).get("cur", {})
        c = d["cf"]["cur"]
        print(d["sha256_prefix"], d["period_type"], d["period_end"], "sc", d.get("scale"), "| rev", i.get("revenue"), "ni", i.get("net_income"), "par", i.get("ni_parent"),
              "| TA", b.get("total_assets"), "TL", b.get("total_liabilities"), "TE", b.get("total_equity"), "| cfo", c.get("cfo"), "cfi", c.get("cfi"), "cff", c.get("cff"),
              "end", c.get("cash_end"), d["sign_notes"] if d.get("sign_notes") else "")
    print("SKIPPED", *skipped, sep="\n  ")
    _, p = ct.check(sym)
    print("PROBLEMS", len(p))
    for x in p:
        print("  ", x)
